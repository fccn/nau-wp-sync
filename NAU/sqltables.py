import logging as log

import mysql.connector

class SQLTables:
	
	def __init__(self, config):
		self.settings = config
		self.connection = None
	
	def status(self):
		return {
			"connected": False if self.connection is None else True
		}
	
	def connect(self):
		
		if self.connection:
			log.debug("Already connected to SQL {host}:{port}".format(host=host, port=port))
			return
		
		host = self.settings.get("host", "localhost")
		port = self.settings.get("port", 3306)
		
		log.debug("Connecting SQL {host}:{port}".format(host=host, port=port))
		
		self.connection = mysql.connector.connect(
			host=host,
			port=port,
			user=self.settings.get("user"),
			passwd=self.settings.get("password"),
			database=self.settings.get("database")
		)
	
	def close(self):
		self.connection.close()
	
	def _getcursor(self, query):
		if not self.connection:
			self.connect()
		
		log.debug("SQL query '%s'" % query)
		return self.connection.cursor()
	
	def query(self, query):  # return a query result set as an list of dicts
		cursor = self._getcursor(query)
		cursor.execute(query)
		description = cursor.description
		
		result = []
		
		for row in cursor.fetchall():
			r = {}
			for idx, column in enumerate(description):
				r[column[0]] = row[idx]
			result.append(r)
		return result
	
	def get(self, query):  # returns only one value on one line
		cursor = self._getcursor(query)
		cursor.execute(query)
		row = cursor.fetchone()
		return row[0]
