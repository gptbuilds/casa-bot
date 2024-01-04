import os
from langchain_core.pydantic_v1 import BaseSettings
import motor.motor_asyncio
from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain.tools import BaseTool
from pydantic import BaseModel, BaseSettings, Field

class MongoDBQuerySchema(BaseModel):
    query: Optional[dict] = Field(default=None, description="MongoDB query.")

class MongoDBQueryTool(BaseTool):
    name: str = "mongo_db_query_properties_tool"
    description: str = "A tool for performing query operations on the 'properties' collection in MongoDB asynchronously."
    args_schema: Type[MongoDBQuerySchema] = MongoDBQuerySchema 

    async def _arun(
        self,
        query: Optional[dict] = None,
    ) -> dict:
        """Query the database with your query. Example document:
            `{
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
            }`"""
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
