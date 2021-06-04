import logging as log
import getopt
import sys
import pprint
import re

from NAU import NAU


def transform_relative_to_absolute_url(url, base_url):
    if url is None:
        return ""
    else:
        if url.startswith('/'):
            return base_url + url
        else:
            return url


def recursive_map(tree, key, map):
    if tree:
        for k, v in tree.items():
            new_key = key + "_" + k
            if isinstance(v, dict):
                recursive_map(v, new_key, map)
            elif isinstance(v, list):
                n = 1
                for i in v:
                    nk = new_key + "_" + "%d" % n
                    recursive_map(i, nk, map)
                    n = n + 1
            else:
                if not ("overview" in new_key):
                    map.update({new_key: v})



def propertiesToSync(course):

    """
    
    keys available at course
    
    created
    modified
    version
    id
    _location
    display_name
    display_number_with_default
    display_org_with_default
    start
    end
    advertised_start
    course_image_url
    social_sharing_url
    end_of_course_survey_url
    certificates_display_behavior
    certificates_show_before_end
    cert_html_view_enabled
    has_any_active_web_certificate
    cert_name_short
    cert_name_long
    lowest_passing_grade
    days_early_for_beta
    mobile_available
    visible_to_staff_only
    _pre_requisite_courses_json
    enrollment_start
    enrollment_end
    enrollment_domain
    invitation_only
    max_student_enrollments_allowed
    announcement
    catalog_visibility
    course_video_url
    effort
    short_description
    org
    self_paced
    marketing_url
    eligible_for_financial_aid
    language
    certificate_available_date
    end_date
    start_date
        
    activeVersion
    about
    Certificates
    Enrollments
    enrollment
 
    """
    
    log.debug("Course Keys Available: {k}".format(k=', '.join([k for k in course])))
    
    youtube_id = ""
    if course['course_video_url']:
        youtube_results = re.compile('v=(.*)').search(course['course_video_url'])
        if youtube_results:
            youtube_id = youtube_results.group(1)
    
    map = dict(
        
        # primary property
        nau_lms_course_id=course["id"],
        nau_lms_course_effort=course['effort'],
    
        nau_lms_course_start=course['start'],
        nau_lms_course_end=course['end'],
        nau_lms_course_enrollment_start=course['enrollment_start'],
        nau_lms_course_enrollment_end=course['enrollment_end'],
        nau_lms_course_advertised_start=course['advertised_start'],
        nau_lms_course_announcement=course['announcement'],
        
        nau_lms_course_name=course['display_name'],
        nau_lms_course_number=course['display_number_with_default'],
        nau_lms_course_org=course['display_org_with_default'],
        nau_lms_course_short_description=course['short_description'],
        
        nau_lms_course_certificate_name = course['cert_name_long'],
        nau_lms_course_visible_to_staff_only=course['visible_to_staff_only'],
    
        nau_lms_course_catalog_visibility=course['catalog_visibility'],
        nau_lms_course_self_paced=course['self_paced'],

        # not working...
        nau_lms_course_language=course['language'],
        
        nau_lms_course_invitation_only=bool(course['invitation_only']),
        nau_lms_course_certificates=int(course['Certificates']),
        nau_lms_course_enrollments=int(course['Enrollments']),
        
        youtube=youtube_id,
        
        # values that could be an url
        nau_lms_course_media_image_raw=course['course_image_url'],
        
        # nau_lms_course_media_course_image=transform_relative_to_absolute_url(course['media']['course_image']['uri'],
        #                                                                     base_url),
        # nau_lms_course_media_course_video=transform_relative_to_absolute_url(course['media']['course_video']['uri'],
        #                                                                     base_url),
        # nau_lms_course_media_image_raw=transform_relative_to_absolute_url(course['media']['image']['raw'], base_url),
        # nau_lms_course_media_image_small=transform_relative_to_absolute_url(course['media']['image']['small'],
        #                                                                    base_url),
        # nau_lms_course_media_image_large=transform_relative_to_absolute_url(course['media']['image']['large'],
        #                                                                    base_url),
    )
    
    if "about" in course:
        recursive_map(course['about'], "nau_course_extra_about", map)
        
    if "enrollment" in course:
        recursive_map(course['enrollment'], "nau_course_enrollment", map)
    
    return map


def merge_data(course_stage, course_prod):
    course_stage['Certificates'] = course_prod['Certificates']
    course_stage['Enrollments'] = course_prod['Enrollments']
    return course_stage


def parseCommandArgs(argv):
    message = "%s [-t] [-c|config <config.yml>] [-d|debug <level>] [-i|i <course-id>]" % (argv[0])
    
    # Default Params
    params = {
        "test": False,
        "debug": None,
        "configfile": "config.yml",
        "course-id": None
    }
    
    try:
        (opts, args) = getopt.getopt(argv[1:], "td:c:i:", ["debug=", "config=", "course="])
    except getopt.GetoptError:
        print(message)
        sys.exit(2)
        
    for opt, arg in opts:
        if opt == '-h':
            print(message)
            sys.exit()
        elif opt in ("-c", "--config"):
            params["configfile"] = arg
        elif opt == '-t':
            params["test"] = True
        elif opt in ("-i", "--course"):
            params["course-id"] = arg
        elif opt in ("-d", "--debug"):
            if arg == "INFO":
                params["debug"] = log.INFO
            elif arg == "DEBUG":
                params["debug"] = log.DEBUG
            elif arg == "WARNING":
                params["debug"] = log.WARNING
            elif arg == "CRITICAL":
                params["debug"] = log.CRITICAL
            elif arg == "ERROR":
                params["debug"] = log.ERROR
            elif arg == "FATAL":
                params["debug"] = log.FATAL
            else:
                params["debug"] = int(arg)
    
    return params

    



def main():
    # Loads Configuration
    nau = NAU(parseCommandArgs(sys.argv))
    
    log.info("Updating data")
    
    lms_courses = []
    if nau.params.get("course-id"):
        course = (nau.lms.getCourse(nau.params.get("course-id")))
        if course:
            lms_courses.append(course)
    else:
        lms_courses = nau.lms.getAllCourses()
    
    if len(lms_courses) == 0:
        log.critical("No courses selected!")
        sys.exit(10)

    log.info("Found {num} courses to update!".format(num=len(lms_courses)))

    for dest_site in nau.getMarketingSites():
        log.info("Updating site {site_name}".format(site_name=dest_site))

        for lms_course in lms_courses:
 
            # Find Course Pages that can be updated with content
            lms_course_id = lms_course["id"]
            course_pages = dest_site.getCoursePageByIDMatchingField(lms_course_id)
            if len(course_pages) > 1:
                log.warning('Duplicated WordPress pages for course id {course_id}'.format(course_id=lms_course_id))

            for course_page in course_pages:

                block_updates = course_page.getField('block-auto-updates')
                if block_updates == '1':
                    # Just skip to next course!
                    log.info('Skipping data retrieval for page {page} on {site_name} as block-auto-updates enabled!' \
                             .format(page=course_page.getId(),
                                     site_name=dest_site))
                    break;
                    
                course_id = course_page.getCourseId()

                log.info('Found {page}@{site_name} from course_id:{course_id}'\
                         .format(page=course_page.getId(),
                                 site_name=dest_site,
                                 course_id=course_id))
                
                course = nau.lms.getCourse(course_id)

                # finds locates and parses AboutData, updates/merges into course
                log.info('Getting course About Data from MongoDB @ {page} {title}' \
                         .format(page=course_page.getId(),
                                 title=course_page.getTitle()))
                course.update(nau.lms.getCourseAboutData(course, nau.mks.getLanguages()))
                course.update(nau.lms.getCourseExtraData(course))
                course.update(nau.lms.getCourseLanguage(course))

                if not 'Certificates' in course.keys():
                    course['Certificates'] = 0
                    
                if not 'Enrollments' in course.keys():
                    course['Enrollments'] = 0

                # verifies changes
                changes, list_of_changes = course_page.syncProperties(course, propertiesToSync)
                if changes > 0:
                    if nau.params.get('test'):
                        log.warning('Test flag enabled! Not changing {page}@{site_name} - {changes} changes found!'.\
                                 format(page=course_page.getId(),
                                        site_name=dest_site,
                                        changes=changes))
                        log.info("Marked for update: " + str(list_of_changes))
                    else:
                        log.warning('Updating {page}@{site_name} - {changes} changes found! {course_page_title}'. \
                                 format(page=course_page.getId(),
                                        site_name=dest_site,
                                        changes=changes,
                                        course_page_title=course_page.getTitle()))
                        log.info("Updating: " + str(list_of_changes))

                        if not dest_site.updateCoursePage(course_page):
                            log.warning('Changes detected, but not updated due to unknown error on {page}@{site_name}'. \
                                format(page=course_page.getId(),
                                       site_name=dest_site))
                else:
                    log.warning('No changes detected on {page}@{site_name}'. \
                                format(page=course_page.getId(),
                                       site_name=dest_site))
    
    

if __name__ == "__main__":
    main()
