import logging as log
import getopt
import sys
import pprint
import re

from NAU import NAU




def parseCommandArgs(argv):
    message = "%s [-c|config <config.yml>] [-d|debug <level>] [-i|i <course-id>] -e|environment <environment>" % (argv[0])
    
    # Default Params
    params = {
        "test": True,
        "debug": None,
        "target_environment": "stage",
        "configfile": "config.yml",
        "course-id": None
    }
    
    try:
        (opts, args) = getopt.getopt(argv[1:], "e:d:c:i:", ["environment=", "debug=", "config=", "course="])
    except getopt.GetoptError:
        print(message)
        sys.exit(2)
        
    for opt, arg in opts:
        if opt == '-h':
            print(message)
            sys.exit()
        elif opt in ("-c", "--config"):
            params["configfile"] = arg
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
    
    log.info("Getting users from : {environment}".format(environment=tenv.getName()))
    
    sql_param = ""
    if nau.params.get("course-id"):
        sql_param = sql_param + " AND coc.id = '{course_id}'".format(course_id=nau.params.get("course-id"))

    pprint.pprint(tenv.lms.SQLQuery("""
        SELECT au.email, au.username, aup.name, COUNT(*) AS referencias
        FROM
            student_courseaccessrole scar,
            auth_user au,
            course_overviews_courseoverview coc,
            organizations_organization oo,
            auth_userprofile aup
        WHERE scar.user_id = au.id
        AND scar.course_id = coc.id
        AND scar.org = oo.short_name
        AND scar.user_id = aup.user_id
        AND scar.role <> 'beta_testers'
        {where_params}
        GROUP BY au.email, au.username, aup.name
    """.format(where_params = sql_param)))
    
    

if __name__ == "__main__":
    main()
