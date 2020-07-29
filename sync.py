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



def propertiesToSync(course, base_url):

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
    activeVersion
    about
    Certificates
    Enrollments
    enrollment
 
    """
    
    log.info("Using {url} as base_url".format(url=base_url))
    
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
        
        nau_lms_course_name=course['display_name'],
        nau_lms_course_number=course['display_number_with_default'],
        nau_lms_course_org=course['display_org_with_default'],
        nau_lms_course_short_description=course['short_description'],
        
        nau_lms_course_certificate_name = course['cert_name_long'],
        nau_lms_course_visible_to_staff_only=course['visible_to_staff_only'],
    
        nau_lms_course_catalog_visibility=course['catalog_visibility'],
        nau_lms_course_self_paced=course['self_paced'],
        
        nau_lms_course_invitation_only=bool(course['invitation_only']),
        nau_lms_course_certificates=int(course['Certificates']),
        nau_lms_course_enrollments=int(course['Enrollments']),
        
        youtube=youtube_id,
        
        # values that could be an url
        nau_lms_course_media_image_raw=transform_relative_to_absolute_url(course['course_image_url'], base_url),
        
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
    message = "%s [-t] [-c|config <config.yml>] [-d|debug <level>] [-i|i <course-id>] -e|environment <environment>" % (argv[0])
    
    # Default Params
    params = {
        "test": False,
        "debug": None,
        "target_environment": "dev",
        "configfile": "config.yml",
        "course-id": None
    }
    
    try:
        (opts, args) = getopt.getopt(argv[1:], "te:d:c:i:", ["environment=", "debug=", "config=", "course="])
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
        elif opt in ("-e", "--environment"):
            params["target_environment"] = arg
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
    
    tenv = nau.getTargetEnvironment()
    
    log.info("Updating data on: {environment}".format(environment=tenv.getName()))
    
    stage_courses = []
    if nau.params.get("course-id"):
        course = (nau.stage.lms.getCourse(nau.params.get("course-id")))
        if course:
            stage_courses.append(course)
    else:
        stage_courses = nau.stage.lms.getAllCourses()
    
    if len(stage_courses) == 0:
        log.critical("No courses selected!")
        sys.exit(10)

    log.info("Found {num} courses to update!".format(num=len(stage_courses)))

    for dest_site in tenv.getMarketingSites():
        log.info("Updating site {site_name}@{environment}".format(site_name=dest_site, environment=tenv))

        for lms_stage_course in stage_courses:
 
            # Find Course Pages that can be updated with content from Stage
            course_page = dest_site.getCoursePageByIDMatchingField(lms_stage_course["id"], 'nau_lms_course_id')
            
            if course_page:
                block_updates = course_page.getField('block-auto-updates')
                if block_updates == '1':
                    # Just skip to next course!
                    log.info('Skipping data retrieval for page {page} on {environment} as block-auto-updates enabled!' \
                             .format(page=course_page.getId(),
                                     environment=tenv))
                    break;
                    
                course_prod_id = course_page.getField('course-id-prod')
                course_stage_id = course_page.getField('nau_lms_course_id') # equal to 'lms_stage_course'

                log.info('Found {page}@{environment} from stage:{stage_id}'\
                         .format(page=course_page.getId(),
                                 environment=tenv,
                                 stage_id=course_stage_id))
                
                course = nau.stage.lms.getCourse(course_stage_id)

                # finds locates and parses AboutData, updates/merges into course
                log.info('Getting course About Data from MongoDB @ {page} {title}' \
                         .format(page=course_page.getId(),
                                 title=course_page.getTitle()))
                course.update(nau.stage.lms.getCourseAboutData(course, nau.stage.mks.getLanguages()))

                got_enrollment_data_from_prod = False
                
                if course_prod_id:
                    # finds and parses extra metadata, if available in prod
                    course_prod = nau.prod.lms.getCourse(course_prod_id)
                    
                    if course_prod:
                        course_prod.update(nau.prod.lms.getCourseExtraData(course_prod))
                        course = merge_data(course, course_prod)
                        
                        log.warning('Merging {page}@{environment} from prod:{prod_id} {enrolls} {certs}' \
                                    .format(page=course_page.getId(),
                                            environment=tenv,
                                            prod_id=course_prod_id,
                                            certs=course["Certificates"],
                                            enrolls=course["Enrollments"]))
                                            
                        log.warning('Merging {page}@{environment} EnrollmentDataAPI from prod:{prod_id}' \
                                    .format(page=course_page.getId(),
                                            environment=tenv,
                                            prod_id=course_prod_id))
                            
                        course.update(nau.prod.lms.getCourseAPIEnrollmentData(course_prod))
                        got_enrollment_data_from_prod = True
                    else:
                        log.warning("Course not found at prod! {prod_id}".format(prod_id = course_prod_id))
                
                
                if not got_enrollment_data_from_prod:
                    # No Prod info, retrieves data from stage!
                    log.warning('Merging {page}@{environment} EnrollmentDataAPI from stage:{stage_id}' \
                                .format(page=course_page.getId(),
                                        environment=tenv,
                                        stage_id=course_stage_id))

                    course.update(nau.stage.lms.getCourseAPIEnrollmentData(course))


                # verifies changes
                changes = course_page.syncProperties(course, propertiesToSync)
                if changes > 0:
                    if nau.params.get('test'):
                        log.warning('Test flag enabled! Not changing {page}@{environment} - {changes} changes found!'.\
                                 format(page=course_page.getId(),
                                        environment=tenv,
                                        changes=changes))
                    else:
                        log.warning('Updating {page}@{environment} - {changes} changes found!'. \
                                 format(page=course_page.getId(),
                                        environment=tenv,
                                        changes=changes))

                        if not dest_site.updateCoursePage(course_page):
                            log.warning('Changes detected, but not updated due to unknow error on {page}@{environment}'. \
                                format(page=course_page.getId(),
                                       environment=tenv))
                else:
                    log.warning('No changes detected on {page}@{environment}'. \
                                format(page=course_page.getId(),
                                       environment=tenv))
    
    

if __name__ == "__main__":
    main()
