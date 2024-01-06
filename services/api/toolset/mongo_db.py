import os
import motor.motor_asyncio
from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

class MongoDBQuerySchema(BaseModel):
    query: Optional[dict] = Field(default=None, description="MongoDB query.")

class MongoDBQueryPropertiesTool(BaseTool):
    name: str = "mongo_db_query_properties_tool"
    description: str = """A tool for performing query operations on the 'properties' collection in MongoDB asynchronously. All properties are in vancouver
    Use this as backup when other tools are insufficient for the request.
        Example document:
            `{{
                "Address": "1006 13387 OLD YALE ROAD",
                "S/A": "Whalley",
                "List Price": "$519,000",
                "Days On Market": "15",
                "Tot BR": "1",
                "Tot Baths": "1",
                "TotFlArea": "495",
                "Yr Blt": "2023",
                "Age": "0",
                "TotalPrkng": "1",
                "MaintFee": "$0.00",
                "TypeDwel": "Apartment/Condo",
                "_id": "6596c6ce7e7ab29d9c7a2dd6",
                "id": "6596c6ce7e7ab29d9c7a2dd6"
            }}`"""
    args_schema: Type[MongoDBQuerySchema] = MongoDBQuerySchema 

    async def _arun(
        self,
        query: Optional[dict] = None,
    ) -> dict:
        """Query the database with your query."""
        client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_CONNECTION_STRING"))
        db = client["casa"]
        collection = db["properties"]
        documents = await collection.find(query).to_list(length=100)
        return {"result": documents}

    async def _run(
        self,
        query: Optional[dict] = None,
    ) -> dict:
        """Not implemented"""
        raise NotImplementedError("Tool does not support sync")

class MongoDBSearchAddressCaseInsensitiveQuerySchema(BaseModel):
    address_search_string: str = Field(description="An address")

class MongoDBSearchAddressCaseInsensitive(BaseTool):
    name: str = "mongo_db_search_address_tool"
    description: str = """A tool for searching through the addresses with a string on the 'properties'. Use this when you need to look for a specific address."""
    args_schema: Type[MongoDBSearchAddressCaseInsensitiveQuerySchema] = MongoDBSearchAddressCaseInsensitiveQuerySchema

    async def _arun(
        self,
        address_search_string: str,
    ) -> dict:
        """Find properties with a similar address"""
        client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_CONNECTION_STRING"))
        db = client["casa"]
        collection = db["properties"]

        query = {
            "Address": {
                "$regex": address_search_string,
                "$options": "i"  # Case-insensitive search
            }
        }

        documents = await collection.find(query).to_list(length=100)

        return {"result": documents}

    async def _run(
        self,
        address_search_string: str,
    ) -> dict:
        """Not implemented"""
        raise NotImplementedError("Tool does not support sync")

