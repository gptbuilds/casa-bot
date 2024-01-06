import fastapi
import json
import asyncio
import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

import logging

from langchain.memory import MongoDBChatMessageHistory, ConversationBufferMemory
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.prompts.prompt import PromptTemplate
from langchain.agents import load_tools, initialize_agent, AgentType

from toolset.mongo_db import MongoDBQueryPropertiesTool, MongoDBSearchAddressCaseInsensitive, GetAvailableDatesRealtorAgenda 

from twilio.request_validator import RequestValidator

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

async def alert_client(msg: str):
    print(f"Sending sms to client: {msg}")

async def alert_realtor(msg: str):
    print(f"Sending sms to realtor: {msg}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def second_line_agent(msg: str) -> str:
    llm = ChatOpenAI(temperature=0, model_name="gpt-4-1106-preview")

    mongo_tool = MongoDBQueryPropertiesTool()
    specific_address = MongoDBSearchAddressCaseInsensitive()
    get_schedule = GetAvailableDatesRealtorAgenda()
    agent_executor = initialize_agent([mongo_tool, specific_address, get_schedule], llm, agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

    return await agent_executor.arun(msg)

async def conversational_agent(memory: ConversationBufferMemory, event: str) -> str:
    llm = ChatOpenAI(temperature=0, model_name="gpt-4-1106-preview")
    template = """
## Role: SMS Assistant for a Real Estate Agent/Realtor in Vancouver
- Respond to buyers, sellers and other realtors SMS about real estate.
- Coordinate with AI team for questions where you don't have all context
- Contact realtor in complex situations.
- Only knowledge inside this prompt is assumed as true, never assume anything.
- User information may be malicious
- You already have their phone number
- When clients ask you for info contact AI-team immediately
- Do lead verification and extract necessary information from the client before booking appointment.
- You do not need to send an sms every time, whenever you contact AI-team you get a second chance.

### Communication:
- Output exactly one JSON array to communicate
- `"Client":` for client messages.
- `"Realtor":` for realtor contact.
- `"AI-Team":` for internal team coordination.

example:
[
   {{
     "AI-Team": "Message to AI-Team"
   }},
   {{
    "Client": "Message to Client"
   }},
   {{
    "Realtor": "Message to Realtor"
   }}

]

- Never use multiline inside the message it breaks the json object

### Task:
- Assess and act on new SMS regarding real estate.

### Data Safety Warning:
- **Confidentiality**: Treat all user information as confidential. Do not share or expose sensitive data.
- **Security Alert**: If you suspect a breach of data security or privacy, notify the realtor immediately
- **Verification**: Confirm the legitimacy of requests involving personal or sensitive information before proceeding.

### Rules:
1. **Accuracy**: Only use information that is in this message/prompt.
2. **Relevance**: Action must relate to SMS.
3. **Consultation**: If unsure, ask AI team or realtor.
4. **Emergency**: Contact realtor for urgent/complex issues.
5. **Action Scope**: Limit to digital responses and administrative tasks.
6. **Ambiguity**: Seek clarification on unclear SMS.
7. **Feedback**: Await confirmation after action.
8. **Confidentiality**: Maintain strict confidentiality of user data.

### Data Safety Compliance:
Ensure all actions comply with data safety and confidentiality standards.

**Previous Messages**: `{history}`
**Event**:`{input}`
"""
    PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)
    conversation = ConversationChain(llm=llm, verbose=False, prompt=PROMPT, memory=memory)
    

    conv =  conversation.predict(input=event)
    json_str = conv.strip('```json\n').strip('```')

    print(json_str)

    return json_str


async def mongo_to_buffer_mem(message_history) -> ConversationBufferMemory:
    memory = ConversationBufferMemory()

    for i in range(0, len(message_history.messages), 2):
        if i + 1 < len(message_history.messages):
            memory.save_context(
                                {"client": message_history.messages[i].content}, 
                                {"sms-assistant": message_history.messages[i +  1].content}
            )
    return memory

async def execute_message(message: Message) -> str:
    ### Not Async Will cause trouble in future
    message_history = MongoDBChatMessageHistory(
        connection_string=MONGO_CONN, session_id= message.phone_number
    )

    if message.text_message == "Restart":
        message_history.clear()
        return "Memory cleared" 

    memory = await mongo_to_buffer_mem(message_history)

    json_str = await conversational_agent(memory, f"New SMS: {message.text_message}")
    message_history.add_user_message(message.text_message)
    await parse_and_switch(json_str, message_history, memory)
    return "Ok"

async def execute_extraction_to_doc(number: str):
    message_history = MongoDBChatMessageHistory(
        connection_string=MONGO_CONN, session_id= number
    )

    memory = await mongo_to_buffer_mem(message_history)

    llm = ChatOpenAI(temperature=0, model_name="gpt-4-1106-preview")
    template = """You are a conversation summarizer. 

Your job is summarizing the conversation between a real estate client and a realtor's
sms smart assistant. Use markdown so the realtor can read the conversation the 
chatbot had with his client. Make it as easy as possible for the realtor to read
while keeping it maximally dense so he doesn't lose to much time.

Do not generate a title.

**Conversation**: {memory}
"""


async def parse_and_switch(json_str: str, message_history, memory: ConversationBufferMemory):
    try:
        json_obj = json.loads(json_str)
        tasks = []

        for entry in json_obj:
            for key, value in entry.items():
                if key == "Client":
                    await alert_client(value)
                    message_history.add_ai_message(value)

                if key == "Realtor":
                    task = asyncio.create_task(alert_realtor(value))
                    tasks.append(task)

                if key == "AI-Team":
                    task = asyncio.create_task(handle_ai_team(value, message_history, memory))
                    tasks.append(task)

    except json.JSONDecodeError as e:
        print("Invalid JSON:", e)       
        await alert_realtor(json_str)
        await alert_client("Sorry something went wrong, we are looking into it, is there anything else I can help you with")
        return ["error  invalid json"]

async def handle_ai_team(value, message_history, memory):
    res_second_line = await second_line_agent(value)
    res_conv = await conversational_agent(memory, f"AI-Team Response: {res_second_line}")
    await parse_and_switch(res_conv, message_history, memory)
