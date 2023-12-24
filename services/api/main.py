import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

import logging

logging.basicConfig(filename='/home/app/logs/print.log', level=logging.INFO, format='%(asctime)s - %(message)s')

app = FastAPI()

class Message(BaseModel):
    phone_number: str 
    text_message: str

@app.get("/ping")
async def ping():
    return "pong"

@app.post("/incoming-sms-hook")
async def receive_form_data(request: Request):
    form_data = await request.form()
    data_dict = dict(form_data)

    logging.info(data_dict)

    return "Ok"

# This will be removed once we go live
@app.post("/only-for-testing-agent")
async def only_for_testing_agent(message: Message):
    #RpfokVcXmxzAedtu
    return "Ok"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
