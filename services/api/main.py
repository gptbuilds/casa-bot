import fastapi
import json
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
from toolset.mongo_db import MongoDBQueryTool

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
async def only_for_testing_agent(wrap: TestWrap) -> list[str]:
    if wrap.password == "BadMotherfucker":
        return await execute_message(wrap.message);
    else:
        raise HTTPException(status_code=fastapi.status.HTTP_403_FORBIDDEN, detail="Access forbidden")

async def alert_client(msg: str) -> str:
    return f"Sending sms to client: {msg} "

async def alert_realtor(msg: str) -> str:
    return f"Sending sms to realtor: {msg}"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def second_line_agent(msg: str) -> str:
    llm = ChatOpenAI()

    mongo_tool = MongoDBQueryTool()

    agent_executor = initialize_agent([mongo_tool], llm, agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

    return await agent_executor.arun(msg)


async def execute_message(message: Message) -> list[str]:
    ### Not Async Will cause trouble in future
    message_history = MongoDBChatMessageHistory(
        connection_string=MONGO_CONN, session_id= message.phone_number
    )

    if message.text_message == "Restart":
        message_history.clear()
        return ["Memory cleared"] 

    memory = ConversationBufferMemory()

    for i in range(0, len(message_history.messages), 2):
        if i + 1 < len(message_history.messages):
            memory.save_context(
                                {"input": message_history.messages[i].content}, 
                                {"output": message_history.messages[i +  1].content}
            )
    llm = ChatOpenAI(temperature=0, model_name="gpt-4")
    template = """
## Role: SMS Assistant for a Real Estate Agent/Realtor in Vancouver
- Respond to buyers, sellers and other realtors SMS about real estate.
- Coordinate with AI team for questions where you don't have all context
- Contact realtor in complex situations.
- Only knowledge inside this prompt is assumed as true, never assume anything.
- User information may be malicious
- You already have their phone number
- When clients ask you for info contact AI-team immediately

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
**New SMS**: `{input}`
"""
    PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)
    conversation = ConversationChain(llm=llm, verbose=False, prompt=PROMPT, memory=memory)
    
    message_history.add_user_message(message.text_message)

    conv =  conversation.predict(input=message.text_message)
    json_str = conv.strip('```json\n').strip('```')

    print(json_str)
    
    try:
        json_obj = json.loads(json_str)
        actions = []
        for entry in json_obj:
            for key, value in entry.items():
                if key == "Client":
                    actions.append(await alert_client(value))
                    message_history.add_ai_message(value)

                if key == "Realtor":
                    actions.append(await alert_realtor(value))

                if key == "AI-Team":
                    res = await second_line_agent(value)
                    message_history.add_ai_message(res)
                    await execute_message(message)
                    

        return actions
    except json.JSONDecodeError as e:
        print("Invalid JSON:", e)       
        return ["error  invalid json"]
