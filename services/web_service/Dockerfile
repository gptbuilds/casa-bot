
FROM python:3.8 


RUN apt-get update && apt-get install -y libpq-dev gcc


COPY . /app
WORKDIR /app


RUN pip install -r requirements.txt


CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8085", "--workers", "4"]
