
CREATE TABLE buildings (
    id      serial PRIMARY KEY,
    name    varchar NOT NULL,
    height  integer NOT NULL,
    city    varchar NOT NULL,
    country varchar NOT NULL
);
