# Wedding Serverless

## Requirements

1. Install python 3.11.4
2. Install Docker

## Setup

### Python Virtual Environment

* Create a virtual env
    * `python -m venv wedding-venv`
* Activate virtual env
    * `source wedding-venv/bin/activate`
* Install dependencies
    * Under root of project run: `pip install -r requirements.txt`

### Database

For local development, the database will run locally in Docker container. Run following commands under `.db/`

#### To Run Database

`docker compose up -d`

## Run Application

`uvicorn app:app --reload`

## Development

### Tech Stack

* [Fast API](https://fastapi.tiangolo.com/)
* Postgres