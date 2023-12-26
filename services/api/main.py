import fastapi
import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import logging
from langchain.memory import MongoDBChatMessageHistory, ConversationBufferMemory
from langchain.llms import OpenAI
from langchain.chains import ConversationChain
from langchain.prompts.prompt import PromptTemplate

logging.basicConfig(filename='/home/app/logs/print.log', level=logging.INFO, format='%(asctime)s - %(message)s')

app = FastAPI()
MONGO_CONN = os.getenv("MONGO_CONNECTION_STRING", "error")

class Message(BaseModel):
    phone_number: str 
    text_message: str

class TestWrap(BaseModel):
    message: Message
    password: str

@app.get("/ping")
async def ping():
    return "pong"

@app.post("/incoming-sms-hook")
async def incoming_sms_hook(request: Request):
    form_data = await request.form()
    data_dict = dict(form_data)

    logging.info(data_dict)

    return "Ok"

# This will be removed once we go live
@app.post("/only-for-testing-agent")
async def only_for_testing_agent(wrap: TestWrap) -> str:
    if wrap.password == "BadMotherfucker":
        return await execute_message(wrap.message);
    else:
        raise HTTPException(status_code=fastapi.status.HTTP_403_FORBIDDEN, detail="Access forbidden")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def execute_message(message: Message) -> str:
    ### Not Async Will cause trouble in future
    message_history = MongoDBChatMessageHistory(
        connection_string=MONGO_CONN, session_id= message.phone_number
    )

    memory = ConversationBufferMemory()

    for i in range(0, len(message_history.messages), 2):
        if i + 1 < len(message_history.messages):
            memory.save_context(
                                {"input": message_history.messages[i].content}, 
                                {"output": message_history.messages[i +  1].content}
            )
    llm = OpenAI(temperature=0.5, model_name="gpt-4-1106-preview")
    template = """You are a part of real estate agent's smart assistant. You are the conversational agent. You have access to a worker agent, he can look things up in the database, or consult the realtor's database.

# Event: You received an sms message.
# Task: Answer the sms message.


Previous Messages:
{history}
New SMS: {input}
"""
    PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)
    conversation = ConversationChain(llm=llm, verbose=False, prompt = PROMPT, memory=memory)
    
    conv =  await conversation.apredict(input=message.text_message)

    message_history.add_user_message(message.text_message)
    message_history.add_ai_message(conv)

    return conv
