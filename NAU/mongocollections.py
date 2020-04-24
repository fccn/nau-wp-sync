import sys

import logging as log

from pymongo import MongoClient, errors

class MongoCollections:
    _collection = ""
    
    def __init__(self, config):
        self.settings = config
        self.connection = None
        self.db = None
    
    def connect(self):
        self.connection = MongoClient(
            host=self.settings.get('host'),
            port=self.settings.get('port'),
            document_class=dict,
            tz_aware=False,
            connect=False
        )
        
        try:
            self.db = self.connection[self.settings.get('db')]
            self.db.authenticate(self.settings.get('user'), self.settings.get('password'))
        except errors.OperationFailure as e:
            log.critical("MongoDB Operation Failure: {msg}".format(msg=e))
            sys.exit(3)
        except errors.ServerSelectionTimeoutError as e:
            log.critical("MongoDB Server Timeout: {msg}".format(msg=e))
            sys.exit(3)
        
    
    def status(self):
        return {
            "connected": False if self.connection is None else True,
            "established": False if self.db is None else True,
            "collection": None if self._collection is None else self._collection,
            "status": "Not Connected" if not self.connection else self.connection.server_info(),
            "collections": self.getCollectionNames()
        }
    
    def getCollectionNames(self):
        if not self.connection:
            self.connect()
        return [collection for collection in self.db.collection_names()]
    
    def collection(self, collection):
        self._collection = collection
        return self
    
    def findOne(self, query, show=None):
        if not self.connection:
            self.connect()
        return self.db[self._collection].find_one(query, show)
    
    def find(self, query, show=None):
        if not self.connection:
            self.connect()
            
        if show is None:
            show = {}
        
        results = []
        
        col = self.db[self._collection]
        
        for result in col.find():
            results.append(result)
        
        return results
