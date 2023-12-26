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
    llm = OpenAI(temperature=0.5)
    template = """The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know.

Current conversation:
{history}
Human: {input}
AI Assistant:"""
    PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)
    conversation = ConversationChain(
                                llm=llm,
                                verbose=False,
                                prompt = PROMPT,
                                memory=memory
                                )
    ## get the result
    conv =  await conversation.apredict(input=message.text_message)
    
    return conv
    

