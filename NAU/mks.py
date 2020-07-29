import sys
import logging as log

from wordpress_xmlrpc import Client, WordPressPage
from wordpress_xmlrpc.methods import posts, media

import mimetypes
import requests
import xmlrpc

from .utils import sanitize_value4log, is_different, sanitize_value


class MarketingSites:
    _sites = None
    
    def __init__(self, config):
        self._sites = {}
        for site in config:
            self._sites[site["id"]] = MarketingSite(site)
    
    def status(self):
        return [site.status() for (key, site) in self._sites.items()]
    
    def getLanguages(self):
        return [site.getLanguage() for (key, site) in self._sites.items()]
    
    def allSites(self):
        return [site for (key, site) in self._sites.items()]
    
    def getSite(self, siteid):
        return self._sites[siteid]


class MarketingSite:
    _connection = None
    _courses = None
    
    def __init__(self, config):
        self.settings = config
        self._url = ''
        self._lms = self.settings.get('lms')
    
    def __str__(self):
        return self.settings["id"]
    
    def url(self):
        if (self._url == ''):
            scheme = self.settings.get('scheme', 'https')
            basic_auth_username = self.settings.get('basic_auth_username')
            basic_auth_password = self.settings.get('basic_auth_password')
            server = self.settings.get('server')
            port = self.settings.get('port', 443)
            path = self.settings.get('wordpress_path', '/xmlrpc.php')
            self._url = "{scheme}://{basic_auth}{server}:{port}{path}".format(
                scheme=scheme,
                basic_auth=('' if basic_auth_username is None else (
                    basic_auth_username + ":" + basic_auth_password + "@")),
                server=server,
                port=port,
                path=path)
        
        return self._url
    
    def get_lms_url(self):
        if self._lms == "":
            log.fatal("No LMS Defined!")
            print("No LMS Defined!")
            exit()
        
        return self._lms
    
    def get_course_path(self, course):
        # lms.stage.nau.fccn.pt/asset-v1:DGE+AFC+2019_20+type@asset+block@IAVE_logo.png
        
        (prefix, courseid) = course["id"].split(":")
        return "/asset-v1:{courseid}+type@asset+block@".format(courseid=courseid)
    
    def getClient(self):
        
        if not self._connection:
            self._connection = Client(self.url(), self.settings["username"], self.settings["password"])
        
        return self._connection
    
    def status(self):
        return {
            'settings': self.settings,
            'url': self.url(),
            'connection': False if not self._connection else True
        }
    
    def getLanguage(self):
        return self.settings["language"]
    
    def getCoursePageByIDMatchingField(self, courseid, tag):
        courses = self.getAllCoursesPages()
        for course in courses:
            if course.getField(tag) == courseid:
                return course
        return False
    
    def getCoursePageWithTag(self, course, tag):
        return self.getCoursePageByID(course["id"], tag)
    
    # https://codex.wordpress.org/XML-RPC_WordPress_API/Posts#wp.getPosts
    def getAllCoursesPages(self, posts_per_request=50):
        
        if not self._courses:
            
            # Get Pages and select Courses
            
            client = self.getClient()
            
            # Get All Pages
            pages = []
            getting_posts = True;
            offset = 0
            while getting_posts:
                log.info("Getting posts from wordpress - number: {number} with offset: {offset}".format(
                    number=posts_per_request, offset=offset))
                current_pages = client.call(
                    posts.GetPosts(
                        {'post_type': 'page',
                         'offset': offset,
                         'number': posts_per_request,
                         }, results_class=WordPressPage))  # CoursePage
                current_pages_len = len(current_pages)
                pages.extend(current_pages)
                offset += posts_per_request
                getting_posts = current_pages_len == posts_per_request
            
            courses = []
            for page in pages:
                if CoursePage.isCourse(page):
                    courses.append(CoursePage(page, self))
            
            self._courses = courses
        
        return self._courses
    
    def updateCoursePage(self, course):
        
        page = course.getWordpressPage()
        
        visibility = course.getField('nau_lms_course_catalog_visibility')
        
        if not visibility:
            visibility = "none"
        
        if visibility.lower() == "none":
            page.status = 'private'
        
        course_image_url = course.getField('nau_lms_course_media_image_raw')
        
        if len(page.thumbnail) == 0 and len(course_image_url) > 0:
            log.info(
                "No thumbnail detected! Uploading new file to media library. {thumb} {url}".format(thumb=page.thumbnail,
                                                                                                   url=course_image_url))
            
            image_response = requests.get(course_image_url)
            image_content = image_response.content
            mimetypes.init()
            imageMimetype = mimetypes.guess_type(course_image_url)[0]
            imageName = course_image_url[course_image_url.rindex('/') + 1:]
            bits = xmlrpc.client.Binary(image_content)
            
            uploadImageResponse = self.getClient().call(
                media.UploadFile({'name': imageName, 'type': imageMimetype, 'bits': bits, 'overwrite': True}))
            attachment_id = uploadImageResponse['id']
            
            page.thumbnail = attachment_id
            
            log.debug("Added page {page_id} new image with id={image_id}".format(page_id=page.id,
                                                                                 image_id=attachment_id))
        
        if not isinstance(page.thumbnail, str):
            page.thumbnail = page.thumbnail['attachment_id']
        
        try:
            self.getClient().call(posts.EditPost(page.id, page))
            log.info("Updated wordpress page with id: " + page.id)
        except ConnectionResetError as e:
            log.critical("HTTP Wordpress Client: {msg}".format(msg=e))
            sys.exit(4)
        except Exception as e:
            log.critical("Unexpected error: {msg}".format(msg=sys.exc_info()[0]))
            log.debug("Skipping... {page_id}".format(page_id=page.id))
            return False
        
        return True


class CoursePage():
    """
    Class that represents a course on open edx with information that should be syncronized
    between the open edx and wordpress platforms.
    """
    
    def __init__(self, wp_page, wp_site):
        
        self._page = wp_page
        self._site = wp_site
        
        log.info("Loaded: {id} {title}".format(id=self.getId(), title=self.getTitle()))
    
    # create private variable containing all course properties to sync
    # self._props = lms_course.properties_to_sync()
    
    def getId(self):
        return self._page.id
    
    def getTitle(self):
        return self._page.title
    
    def getWordpressPage(self):
        return self._page
    
    def getField(self, key):
        
        for page_custom_field in self._page.custom_fields:
            page_custom_field_key = page_custom_field['key']
            if key == page_custom_field_key:
                return page_custom_field['value']
        
        return None
    
    def meta(self):
        return {
            'post_id': self._page.post_id,
            'title': self._page.title,
            # 'fields': self._page["custom_fields"],
            # 'isCourse': self.isCourse(), # doesn't make sense anymore
            'isProdSyncable': self.isProdSyncable(),
            'isStageSyncable': self.isStageSyncable(),
            # 'terms': self._page['terms']
        }
    
    def isCourse(page):
        # Is course based on category?
        for term in page.terms:
            if term.slug == 'curso':
                return True
        return False
    
    def isProdSyncable(self):
        for custom_field in self._page["custom_fields"]:
            if custom_field['key'] == 'course-id-prod':
                return custom_field['value'] if custom_field['value'] != '' else False
        
        return False
    
    def isStageSyncable(self):
        for custom_field in self._page["custom_fields"]:
            if custom_field['key'] == 'nau_lms_course_id':
                return custom_field['value'] if custom_field['value'] != '' else False
        
        return False
    
    def syncProperties(self, course, properties_to_sync):
        
        log.debug("Synchronizing wordpress page with id: " + self.getId())
        changes_count = 0
        list_of_changes = []
        
        auto_update = self.getField('update-overview')
        if auto_update == '1':
            
            log.info('Preparing content for update @ {page} {title}' \
                     .format(page=self.getId(),
                             title=self.getTitle()))
            new_content = self.getContent(course)
            if not self._page.content == new_content:
                log.info('New content found! Marked for update @ {page} {title}' \
                         .format(page=self.getId(),
                                 title=self.getTitle()))
                self._page.content = new_content
                changes_count += 1
        else:
            log.warning('Auto Update Disabled, skipping content update @ {page} {title}' \
                        .format(page=self.getId(),
                                title=self.getTitle()))
        
        for (name, value) in properties_to_sync(course, self._site.get_lms_url()).items():
            course_property_found = False
            value = sanitize_value(value)
            
            for page_custom_field in self._page.custom_fields:
                if name == page_custom_field['key']:
                    course_property_found = True
                    break
            
            if course_property_found:  # if field found
                # Located Field, updating
                log.debug("Checking field: {field} : {value}".format(field=name, value=sanitize_value4log(
                    page_custom_field['value'])))
                if is_different(page_custom_field['value'], value):  # if different value, update whatever the value
                    last_value = page_custom_field['value']
                    page_custom_field['value'] = value
                    changes_count += 1
                    list_of_changes.append(name)
                    log.debug(
                        "Update page {id} width field ({key}) with value: «{value}» was «{last}»".format(
                            id=self._page.id, key=name, value=sanitize_value4log(value),
                            last=sanitize_value4log(last_value)))
            else:
                if value:  # if not empty, create field with value. Skip if no value.
                    self._page.custom_fields.append({
                        'key': name,
                        'value': value
                    })
                    changes_count += 1
                    list_of_changes.append(name)
                    log.debug("Add page {id} field ({key}) with value: «{value}»".format(
                        id=self._page.id,
                        key=name,
                        value=sanitize_value4log(value)))
        
        if auto_update:
            excerpt = course['short_description']
            if not self._page.excerpt == excerpt:
                log.info('New excerpt found! Marked for update @ {page} {title}' \
                         .format(page=self.getId(),
                                 title=self.getTitle()))
                self._page.excerpt = excerpt
                changes_count += 1
                list_of_changes.append('excerpt')
        
        return changes_count, list_of_changes
    
    def getContent(self, course):
        
        lang = self._site.getLanguage()
        
        content = course['about']['overview']
        
        if 'overview' in course['about']['mks'][lang]:
            content = course['about']['mks'][lang]['overview']
        
        content = content \
            .replace("=\"/static/",
                     "=\"{lms}".format(lms=self._site.get_lms_url() + self._site.get_course_path(course))) \
            .replace("src=\"/", "src=\"{lms}".format(lms=self._site.get_lms_url() + self._site.get_course_path(course))) \
            .replace(" style=\"", " style-disable=\"")
        
        return content
