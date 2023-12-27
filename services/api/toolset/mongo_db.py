from langchain_core.tools import BaseTool
from langchain.document_loaders.mongodb import MongodbLoader
from pymongo import MongoClient


class MongoDBTool(BaseTool):
    """
    A tool for working with MongoDB collections.
    """

    def __init__(self, connection_string, db_name, collection_name):
        """
        Initialize the MongoDBTool.

        Args:
            connection_string (str): The connection string for the MongoDB database.
            db_name (str): The name of the MongoDB database.
            collection_name (str): The name of the MongoDB collection.
        """
        super(connection_string, db_name).__init__()
        self.connection_string = connection_string
        self.db_name = db_name
        self.collection_name = collection_name

    async def load_documents(self):
        """
        Load documents from the MongoDB collection.

        Returns:
            list: The loaded documents.
        """
        loader = MongodbLoader(
            connection_string=self.connection_string,
            db_name=self.db_name,
            collection_name=self.collection_name,
        )
        return await loader.aload()

    from pymongo import MongoClient

    async def insert_documents(self, documents):
        """
        Insert documents into the MongoDB collection.

        Args:
        documents (list): The documents to insert.
        """
        client = MongoClient(self.connection_string)
        db = client[self.db_name]
        collection = db[self.collection_name]
        collection.insert_many(documents)

    async def update_documents(self, filter, update):
        """
        Update documents in the MongoDB collection.

        Args:
            filter (dict): The filter to match documents for update.
            update (dict): The update object.
        """
        client = MongoClient(self.connection_string)
        db = client[self.db_name]
        collection = db[self.collection_name]
        collection.update_many(filter, update)
    
    async def delete_documents(self, filter):
        """
        Delete documents from the MongoDB collection.

        Args:
            filter (dict): The filter to match documents for deletion.
        """
        client = MongoClient(self.connection_string)
        db = client[self.db_name]
        collection = db[self.collection_name]
        collection.delete_many(filter)

    async def query_documents(self, query):
        """
        Query documents from the MongoDB collection.

        Args:
            query (dict): The query object.

        Returns:
            list: The matching documents.
        """
        client = MongoClient(self.connection_string)
        db = client[self.db_name]
        collection = db[self.collection_name]
        result = collection.find(query)

        return list(result)
