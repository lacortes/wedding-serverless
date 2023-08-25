import datetime
import enum
from typing import Annotated, Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel, BaseSettings
from sqlalchemy.engine import URL
from sqlmodel import create_engine, SQLModel, Session, select, col, Field

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Settings(BaseSettings):
    db_username: str
    db_password: str
    db_host: str
    db_database: str

    class Config:
        env_file = '.env.production', '.env.dev', '.env'
        env_file_encoding = 'utf-8'


settings = Settings()


class RSVP(str, enum.Enum):
    attending = 'ATTENDING'
    not_attending = 'NOT_ATTENDING'
    pending = 'PENDING'


class Guest(SQLModel, table=True):
    guest_id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    guest_type: str
    avail_guests: int
    rsvp: str
    updated_at: datetime.datetime


class GuestUpdate(BaseModel):
    first_name: Annotated[str, Field(min_length=3, max_length=20, regex="[a-zA-Z]")]
    last_name: Annotated[str, Field(min_length=3, max_length=20, regex="[a-zA-Z]")]
    rsvp: RSVP


@app.get("/")
async def get_settings():
    return {"message": settings.dict()}


@app.get("/v1/guests", response_model=Guest)
async def get_guest(
        first_name: Annotated[str, Query(min_length=3, max_length=20, regex="[a-zA-Z]")],
        last_name: Annotated[str, Query(min_length=3, max_length=20, regex="[a-zA-Z]")],
):
    guest = get_guest_db(first_name.lower(), last_name.lower())
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest


@app.put("/v1/guests", response_model=Guest)
async def update_guest(guest: GuestUpdate):
    guest_db = get_guest_db(guest.first_name.lower(), guest.last_name.lower())
    if guest_db is None:
        raise HTTPException(status_code=404, detail="Guest not found")

    guest_db.rsvp = guest.rsvp

    update_guest_db(guest_db)

    return guest_db


engine = create_engine(
    URL.create(
        drivername="postgresql",
        username=settings.db_username,
        password=settings.db_password,
        host=settings.db_host,
        database=settings.db_database,
        port=5432
    ),
    echo=True
)


def get_guest_db(first_name: str, last_name: str):
    with Session(engine) as session:
        statement = select(Guest).where(col(Guest.first_name) == first_name, col(Guest.last_name) == last_name)
        results = session.exec(statement)
        return results.first()


def update_guest_db(guest: Guest):
    with Session(engine) as session:
        session.add(guest)
        session.commit()
        session.refresh(guest)


handler = Mangum(app)
