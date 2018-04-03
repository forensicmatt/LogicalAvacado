import ujson
import hashlib
import logging
from arango import ArangoClient


class ArangoHandler(object):
    def __init__(self, database, protocol='http', host='localhost', port=8529, username='root', password=''):
        self.BATCH_LIMIT = 10000
        self.client = ArangoClient(
            protocol=protocol,
            host=host,
            port=port,
            username=username,
            password=password,
            enable_logging=True
        )
        self.db = self.retrieve_db(
            database
        )

    def retrieve_db(self, database_name):
        if self.has_db(database_name):
            return self.client.database(
                database_name
            )
        else:
            return self.client.create_database(
                database_name
            )

    def has_db(self, database_name):
        database_list = self.client.databases()
        if database_name in database_list:
            return True
        else:
            return False

    def insert_jsonl(self, collection_name, lines):
        collection = self.retrieve_collection(
            collection_name
        )

        commit = []
        lines = lines.split(b"\n")
        count = 0
        for line in lines:
            try:
                dictionary = ujson.loads(line)
            except Exception as error:
                logging.error(u"Error loading jsonl: {}".format(line))
                line = lines.pop()
                continue

            key_hash = hashlib.md5(line)
            dictionary['_key'] = key_hash.hexdigest()
            commit.append(dictionary)

            if len(commit) == self.BATCH_LIMIT:
                collection.import_bulk(commit, sync=True, on_duplicate="ignore")
                commit[:] = []

            count += 1

        if len(commit) > 0:
            collection.import_bulk(commit, sync=True, on_duplicate="ignore")

        logging.info(u"Records Processed: {}".format(count))

    def retrieve_collection(self, collection_name):
        if self.has_collection(collection_name):
            return self.db.collection(collection_name)
        else:
            return self.db.create_collection(collection_name)

    def has_collection(self, collection_name):
        collection_list = self.db.collections()
        for collection_info in collection_list:
            if collection_info['name'] == collection_name:
                return True
        return False
