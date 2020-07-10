import logging as log
import lxml.html as html

from .sqltables import SQLTables
from .mongocollections import MongoCollections
from .api import OpenEDXAPI
from .mks import MarketingSite


def convertDict(lista):
    d = {}
    for item in lista:
        d[item['tag']] = item['value']
    return d


def _parseCourseID(courseid):
    (base, id) = courseid.split(":")
    return id.split("+")


class LMS:
    
    def __init__(self, config):
        self.settings = config
        self._sql = SQLTables(config.get('db'))
        self._mongo = MongoCollections(config.get('mongo'))
        self._api = OpenEDXAPI(config.get('api'))
    
    def status(self):
        return {
            'settings': self.settings,
            'sql': self._sql.status(),
            'mongo': self._mongo.status(),
            'api': self._api.status(),
        }
    
    def SQLQuery(self, sql):
        return self._sql.query(sql);
    
    def SQLgitGet(self, sql):
        return self._sql.get(sql);
    
    def getOrganizations(self):
        return self._sql.query("SELECT * from organizations_organization")
    
    def getCourse(self, course):
        log.info("getCourse %s" % course)
        course = self._sql.query("SELECT * from course_overviews_courseoverview WHERE id='%s'" % (course))
        if len(course) == 1:
            return course[0]
        
        return None
    
    def getAllCoursesFromOrganization(self, organization):
        return self._sql.query("SELECT * FROM course_overviews_courseoverview WHERE org='%s'" % (organization))
    
    def getAllCourses(self):
        return self._sql.query("SELECT * FROM course_overviews_courseoverview")
        
    def getCourseExtraData(self, course):
        r = {
            "Enrollments": self._sql.get(
                "SELECT count(*) FROM student_courseenrollment WHERE course_id = '%s'" % (course["id"])),
            "Certificates": self._sql.get(
                "SELECT count(*) FROM certificates_generatedcertificate WHERE course_id = '%s'" % (course["id"])),
        }
        
        log.info("Course {id} | Enrollments = {enrolls} | Certificates = {certs}".format(id=course["id"], enrolls=r["Enrollments"],certs=r["Certificates"]))
        
        return r
    
    def getAllCoursesAPIData(self):
        return self._api.getCourses()
 
    def getCourseAPIData(self, course):
        return self._api.getCourseData(course["id"])

    def getCourseAPIEnrollmentData(self, course):
        return {"enrollment": self._api.getEnrollmentData(course["id"])}

    def getCourseActiveVersion(self, course):
        log.info("Getting ID: %s" % (course["id"]))
        (org, course, run) = _parseCourseID(course["id"])
        return self._mongo.collection("modulestore.active_versions").findOne({"org": org, "course": course, "run": run})
    
    def getCourseStructure(self, id):
        return self._mongo.collection("modulestore.structures").findOne(
            {"_id": id})
    
    def getCourseDefinition(self, id):
        return self._mongo.collection("modulestore.definitions").findOne(
            {"_id": id})
    
    def getCourseAboutFromActiveVersion(self, active_course):
        structure = self.getCourseStructure(active_course["versions"]["published-branch"])
        about = []
        
        for block in structure["blocks"]:
            if (block['block_type'] == 'about'):
                about.append({
                    "tag": block['block_id'],
                    "value": self.getCourseDefinition(block["definition"])["fields"]["data"]
                })
        return about
    
    def getCourseAboutData(self, base_course, languages):
        
        course = {}
        course["activeVersion"] = self.getCourseActiveVersion(base_course)
    
        # retrieves about details based on activeversion
        course["about"] = convertDict(self.getCourseAboutFromActiveVersion(course["activeVersion"]))
    
        # processes "about"/"overview", finding sections "pt_PT" and "en_US" with inner blocks
    
        course["about"]["mks"] = {}
    
        for lang in languages:
            course["about"]["mks"][lang] = {}
            for lang_child in html.fromstring(course["about"]["overview"]).xpath("//section[@class='%s']/*" % lang):
                course["about"]["mks"][lang][lang_child.xpath("@class")[0]] = lang_child.xpath("node()")[0]
    
        return course

