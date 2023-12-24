import uvicorn
from fastapi import FastAPI, Request
import logging

logging.basicConfig(filename='/home/app/logs/print.log', level=logging.INFO, format='%(asctime)s - %(message)s')

app = FastAPI()


@app.get("/ping")
async def ping():
    return "pong"

@app.post("/incoming-sms-hook")
async def receive_form_data(request: Request):
    form_data = await request.form()
    data_dict = dict(form_data)

    logging.info(data_dict)

    return "Ok"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
