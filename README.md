# casa-bot

A real estate whatsapp/sms bot using twilio and langchain.

## Dev

`docker compose up --build`

To smoke test:

`curl -H Host:fastapi.localhost http://0.0.0.0:81`

Note it's running on port 81 because I had some other service running on
port 80 already. This is not the case in prod.

## Prod

`docker-compose -f docker-compose.prod.yml up --build`

To smoke test:

`curl https://subdomain.example.com`

Make sure you set up traefik and let's encrypt for your domain.
