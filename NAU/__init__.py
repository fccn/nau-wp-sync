import logging as log
import logging.config

import json
import yaml

from .openedx import LMS
from .mks import MarketingSites

class NAU:
	def __init__(self, params):
		
		self.params = params
		filename = self.params["configfile"]
		
		# Read YAML file
		log.debug("Reading file {file}".format(file=filename))
		with open(filename, 'r') as config_data_stream:
			config = yaml.safe_load(config_data_stream)
		
		self.config = config["general"]
		
		if params["debug"]:
			# Override debug from config file!
			self.config["logging"]["handlers"]["console"]["level"] = params["debug"]
		
		# https://www.digitalocean.com/community/tutorials/how-to-use-logging-in-python-3
		# https://docs.python.org/3/library/logging.config.html#logging-config-dictschema
		logging.config.dictConfig(self.config.get('logging'))
		
		self.lms = LMS(config["lms"])
		self.mks = MarketingSites(config["mks"])
		
		log.info("NAU Configured!")
		log.debug(self.config)
		log.debug(self.params)
	
	def getLanguages(self):
		return self.mks.getLanguages()
	
	def getMarketingSites(self):
		return self.mks.allSites()
	
	def status(self):
		return {
			'name': self.getName(),
			'lms': self.lms.status(),
			'mks': self.mks.status()
		}

	def __str__(self):
		return json.dumps(self.status())
	