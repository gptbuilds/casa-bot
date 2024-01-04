import motor.motor_asyncio
from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

class MongoDBQuerySchema(BaseModel):
    query: Optional[dict] = Field(default=None, description="MongoDB query.")

class MongoDBQueryTool(BaseTool):
    name: str = "mongo_db_query_properties_tool"
    description: str = "A tool for performing query operations on the 'properties' collection in MongoDB asynchronously."
    args_schema: Type[MongoDBQuerySchema] = MongoDBQuerySchema

    def __init__(self, mongo_uri):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        self.db = self.client["casa"]
        self.collection = self.db["properties"]

    async def _arun(
        self,
        query: Optional[dict] = None,
    ) -> dict:
        documents = await self.collection.find(query).to_list(length=100)
        return {"result": documents}
