CREATE TYPE attendance as ENUM ('ATTENDING', 'NOT_ATTENDING', 'PENDING');
CREATE TYPE guest_type as ENUM ('PRIMARY', 'SECONDARY');
CREATE TABLE guest
(
    guest_id     SERIAL PRIMARY KEY,
    first_name   VARCHAR(50) NOT NULL,
    last_name    VARCHAR(50) NOT NULL,
    guest_type   guest_type  NOT NULL DEFAULT 'PRIMARY',
    rsvp         attendance  NOT NULL DEFAULT 'PENDING',
    selection    smallint    NOT NULL DEFAULT 0 CHECK ( selection >= 0 AND selection <= 2),
    avail_guests INTEGER     NOT NULL DEFAULT 0,
    created_at   timestamp   NOT NULL DEFAULT NOW(),
    updated_at   timestamp   NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_fullname ON guest (first_name, last_name);

CREATE TABLE secondary_guest
(
    guest_id         SERIAL PRIMARY KEY,
    primary_guest_id INT REFERENCES guest (guest_id) ON DELETE CASCADE,
    first_name       VARCHAR(50) NOT NULL,
    last_name        VARCHAR(50) NOT NULL,
    rsvp             attendance  NOT NULL DEFAULT 'PENDING',
    selection        smallint    NOT NULL DEFAULT 0 CHECK ( selection >= 0 AND selection <= 2),
    created_at       timestamp   NOT NULL DEFAULT NOW(),
    updated_at       timestamp   NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_fullname_secondary ON secondary_guest (first_name, last_name);