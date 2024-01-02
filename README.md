# casa-bot

A real estate sms bot using twilio and langchain.

## Dev

docker compose up --build

docker exec -it casa-bot-1-db-1 psql -U mcd0056 -d mydb

Run SQL command
CREATE TABLE IF NOT EXISTS properties (
    id SERIAL PRIMARY KEY,
    position INT,
    price VARCHAR(100),
    bedrooms VARCHAR(50),
    bathroom VARCHAR(50),
    area_sqft VARCHAR(100),
    description TEXT,
    address TEXT,
    other_info TEXT,
    image_url TEXT,
    detail_link TEXT
);

run main.py in Database\DB_Script to upload data to DB

docker compose down 
docker compose up -d

query DB
curl --location 'http://localhost:8085/properties' \
--data ''

Test Agent

curl --location 'http://fastapi.localhost:81/only-for-testing-agent' \
--header 'Content-Type: application/json' \
--data '{
           "message": {
             "phone_number": "9995623",
             "text_message": "Can you talk with the AI Team and Find a house with 3 bedrooms?"
           },
           "password": "BadMotherfucker"
         }'



## Prod

`docker-compose -f docker-compose.prod.yml up --build`

To smoke test:

`curl https://subdomain.example.com`

Make sure you set up traefik and let's encrypt for your domain.
