import logging as log
import logging.config

import json
import yaml

from .openedx import LMS
from .mks import MarketingSites


class Environment():
	
	def __init__(self, name, config):
		self.name = name
		self.lms = LMS(config["lms"])
		self.mks = MarketingSites(config["mks"])
	
	def __str__(self):
		return self.getName()
	
	def getName(self):
		return self.name
	
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


class NAU:
	stage = None
	prod = None
	
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
		
		self.stage = Environment("stage", config["stage"])
		self.prod = Environment("prod", config["prod"])
		
		log.info("NAU Configured!")
		log.debug(self.config)
		log.debug(self.params)
	
	def status(self):
		return {
			'general': self.config,
			'stage': self.stage.status(),
			'prod': self.prod.status(),
		}
	
	def __str__(self):
		return json.dumps(self.status())
	
	def getTargetEnvironment(self):
		
		if self.params.get("target_environment") == "stage":
			return self.stage
		
		if self.params.get("target_environment") == "prod":
			return self.prod
		
		raise NameError('Unknown Environment')
