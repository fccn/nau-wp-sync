import logging as log
import getopt
import sys
import pprint

from NAU import NAU

def parseCommandArgs(argv):
	message = "%s [-c|config <config.yml>] [-d|debug <level>] [-i|i <course-id>] -e|environment <environment>" % (
		argv[0])
	
	# Default Params
	params = {
		"test": True,
		"debug": None,
		"target_environment": "prod",
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
	
	if not params["course-id"]:
		print("No course defined!")
		print(message)
		sys.exit()
	
	return params


def main():
	# Loads Configuration
	nau = NAU(parseCommandArgs(sys.argv))
	
	tenv = nau.getTargetEnvironment();
	course = nau.params.get("course-id");
	
	log.info("Getting users from : {course}@{environment}".format(course=course, environment=tenv.getName()))
	
	pprint.pprint(tenv.lms.SQLQuery("""
        SELECT au.id AS user_id, au.email, au.username, cgc.modified_date AS CertificateDate, grade * 100 AS Percentage, cgc.`mode`, cgc.`status`, sce.`mode`, sce.is_active
          FROM auth_user au
		  LEFT JOIN student_courseenrollment sce ON au.id = sce.user_id
		  LEFT JOIN certificates_generatedcertificate cgc ON au.id = cgc.user_id
		 WHERE 1 = 1
		   AND sce.course_id = '{course}'
           AND cgc.course_id = sce.course_id
    """.format(course=course)))


if __name__ == "__main__":
	main()
