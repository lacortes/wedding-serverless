import datetime
import enum
from typing import Annotated, Optional, List

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel, BaseSettings, conint, root_validator
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
    selection: int
    updated_at: datetime.datetime


class SecondaryGuest(SQLModel, table=True):
    __tablename__ = 'secondary_guest'

    guest_id: Optional[int] = Field(default=None, primary_key=True)
    primary_guest_id: Optional[int] = Field(default=None, foreign_key="guest.guest_id")
    first_name: str
    last_name: str
    rsvp: str
    selection: int


class GuestUpdate(BaseModel):
    first_name: Annotated[str, Field(min_length=3, max_length=20, regex="[a-zA-Z]")]
    last_name: Annotated[str, Field(min_length=3, max_length=20, regex="[a-zA-Z]")]
    rsvp: RSVP


class RsvpGuest(BaseModel):
    first_name: Annotated[str, Field(min_length=3, max_length=20, regex="[a-zA-Z]")]
    last_name: Annotated[str, Field(min_length=3, max_length=20, regex="[a-zA-Z]")]
    rsvp: RSVP
    selection: conint(ge=0, le=2)

    @root_validator
    def check_selection(cls, values):
        rsvp, selection = values.get('rsvp'), values.get('selection')
        if rsvp == RSVP.not_attending and selection != 0:
            raise ValueError('Cannot make a selection if not attending')
        if rsvp == RSVP.attending and selection == 0:
            raise ValueError('Cannot attend and have no selection')
        return values


class RsvpCreate(BaseModel):
    guest: RsvpGuest
    party: List[RsvpGuest] = []


@app.get("/v1/guests", response_model=Guest)
async def get_guest(
        first_name: Annotated[str, Query(min_length=2, max_length=20, regex="[a-zA-Z]")],
        last_name: Annotated[str, Query(min_length=2, max_length=20, regex="[a-zA-Z]")],
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


@app.post("/v1/guests/rsvp")
async def create_rsvp(rsvp: RsvpCreate):
    guest_db = get_guest_db(rsvp.guest.first_name.lower(), rsvp.guest.last_name.lower())
    if guest_db is None:
        print()
        raise HTTPException(status_code=404, detail="Primary Guest not found")

    if guest_db.rsvp != RSVP.pending or rsvp.guest.rsvp == guest_db.rsvp:
        raise HTTPException(status_code=409, detail="Cannot create rsvp for an already created rsvp")

    if (rsvp.guest.rsvp == RSVP.attending and guest_db.avail_guests <= 0 < len(rsvp.party)
            or guest_db.avail_guests < len(rsvp.party)):
        raise HTTPException(
            status_code=400,
            detail=f"{guest_db.first_name} {guest_db.last_name} has disallowed guests."
        )

    guest_db.avail_guests -= len(rsvp.party)
    guest_db.selection = rsvp.guest.selection
    guest_db.rsvp = rsvp.guest.rsvp
    guest_db.updated_at = datetime.datetime.now()
    update_guest_db(guest_db)

    if len(rsvp.party) > 0:
        guests = [SecondaryGuest(**g.dict(), primary_guest_id=guest_db.guest_id) for g in rsvp.party]
        add_secondary_guests(guests)

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


def add_secondary_guests(guests: list[SecondaryGuest]):
    with Session(engine) as session:
        for guest in guests:
            session.add(guest)

        session.commit()


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
