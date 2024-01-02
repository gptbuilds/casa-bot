FROM python:3.8


RUN apt-get update && apt-get install -y libpq-dev gcc

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8085", "app:app"]
