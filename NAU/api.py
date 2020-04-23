import logging as log
import json, urllib.request


class OpenEDXAPI():
    
    def __init__(self, config):
        self.settings = config
        self._api_courses_path = config.get('api_courses_path', '/api/courses/v1/courses/')
        self._api_enrollment_path = config.get('api_enrollment_path', '/api/enrollment/v1/course/')
        self._scheme = config.get('scheme', 'https')
        self._server = config.get('server')
        self._courses = None
    
    def status(self):
        return {
            "settings": self.settings,
            "api_courses_path": self._api_courses_path,
            "api_enrollment_path": self._api_courses_path,
            "scheme": self._scheme,
            "server": self._server,
            "courses": len(self._courses)
        }
    
    def url(self, api_path):
        return "{scheme}://{server}{api_path}".format(
            scheme=self._scheme,
            server=self._server,
            api_path=api_path
        )
    
    def getCourses(self, refresh=False):
        
        if (self._courses is None) or refresh:
            
            url = self.url(self._api_courses_path)
            
            print("Loading lms courses from json url: {url} ".format(url=url))
            
            courses = []
            # iterate each lms page for each load its content to LmsCourse class
            
            next_url = url
            
            while True:
                response = urllib.request.urlopen(next_url)
                str_response = response.read().decode('utf-8')
                output = json.loads(str_response)
                
                for lms_course_data in output['results']:
                    courses.append(lms_course_data)
                
                pagination = output['pagination']
                n = pagination['next']
                if n is not None:
                    next_url = n
                else:
                    break
            
            self._courses = courses
        
        print(self._courses)
        
        return self._courses
    
    def getCourseData(self, course_id):
        
        for course in self.getCourses():
            if course["course_id"] == course_id:
                return course
        
        return None
    
    def getEnrollmentData(self, course_id):

        url = self.url(self._api_enrollment_path + course_id)
    
        log.info("Getting getEnrollmentData %s" % url)
    
        try:
            response = urllib.request.urlopen(url)
            str_response = response.read().decode('utf-8')

            log.debug("Returned data: %s" % str_response)
            return json.loads(str_response)
            
        except urllib.error.HTTPError as e:
            log.error("Message back from API server looking for {course}: {code}:{reason}".format(course=course_id, code=e.code, reason=e.reason))
            
        return None
        
        



        
