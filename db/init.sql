CREATE TYPE attendance as ENUM ('ATTENDING', 'NOT_ATTENDING', 'PENDING');
CREATE TYPE guest_type as ENUM ('PRIMARY', 'SECONDARY');
CREATE TABLE guest(
    guest_id  SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    guest_type guest_type NOT NULL DEFAULT 'PRIMARY',
    rsvp attendance NOT NULL DEFAULT 'PENDING',
    avail_guests INTEGER NOT NULL DEFAULT 0,
    created_at timestamp NOT NULL DEFAULT NOW(),
    updated_at timestamp NOT NULL DEFAULT NOW()
);