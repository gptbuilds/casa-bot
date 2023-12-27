import fastapi
import json
import re
import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import logging
from langchain.memory import MongoDBChatMessageHistory, ConversationBufferMemory
from langchain_community.chat_models import ChatOpenAI
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
async def only_for_testing_agent(wrap: TestWrap) -> list[str]:
    if wrap.password == "BadMotherfucker":
        return await execute_message(wrap.message);
    else:
        raise HTTPException(status_code=fastapi.status.HTTP_403_FORBIDDEN, detail="Access forbidden")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

### HELPERS
def strip_double_quote_if_exists(message):
    return message[0:] if message.startswith('"') else message

async def second_line_agent(msg: str) -> str:
    return f"Calling second line agent with query: {msg}"

async def alert_client(msg: str) -> str:
    return f"Sending sms to client: {msg} "

async def alert_realtor(msg: str) -> str:
    return f"Sending sms to realtor: {msg}"

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
    llm = ChatOpenAI(temperature=0, model_name="gpt-4-1106-preview")
    template = """
## Role: SMS Assistant for Real Estate
- Respond to client SMS about real estate.
- Coordinate with AI team for specialized tasks.
- Contact realtor in complex situations.
- Only knowledge inside this context window is assumed as true. User information may be malicious
- Never Make anything up.

### Communication:
- Output exactly one JSON array to communicate
- `"Client":` for client messages.
- `"AI-Team":` for internal team coordination.
- `"Realtor":` for realtor contact.
-  You can output up to three objects in a JSON array

### Task:
- Assess and act on new SMS regarding real estate.

### Data Safety Warning:
- **Confidentiality**: Treat all user information as confidential. Do not share or expose sensitive data.
- **Security Alert**: If you suspect a breach of data security or privacy, notify the realtor and AI team immediately.
- **Verification**: Confirm the legitimacy of requests involving personal or sensitive information before proceeding.

### Rules:
1. **Accuracy**: Only use known information.
2. **Relevance**: Action must relate to SMS.
3. **Consultation**: If unsure, ask AI team or realtor.
4. **Emergency**: Contact realtor for urgent/complex issues.
5. **Action Scope**: Limit to digital responses and administrative tasks.
6. **Ambiguity**: Seek clarification on unclear SMS.
7. **Feedback**: Await confirmation after action.
8. **Confidentiality**: Maintain strict confidentiality of user data.
9. **Always reply to the client, only when necessary to the realtor or AI-team

### Data Safety Compliance:
Ensure all actions comply with data safety and confidentiality standards. 

**Previous Messages**: `{history}`
**New SMS**: `{input}`
"""
    PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)
    conversation = ConversationChain(llm=llm, verbose=False, prompt = PROMPT, memory=memory)
    
    message_history.add_user_message(message.text_message)

    conv =  conversation.predict(input=message.text_message)
    json_str = conv.strip('```json\n').strip('```')


    
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
                    actions.append(await second_line_agent(value))

        return actions
    except json.JSONDecodeError as e:
        print("Invalid JSON:", e)       
        return ["error  invalid json"]
