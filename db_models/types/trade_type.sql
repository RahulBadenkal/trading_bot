DROP TYPE IF EXISTS trade_type;
CREATE TYPE trade_type AS (
    id uuid,
    alert_id uuid,
    coin VARCHAR,
    status VARCHAR,
    fired_on timestamp
);
