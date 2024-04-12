CREATE TABLE alert (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    coin VARCHAR NOT NULL,
    "action" VARCHAR NOT NULL CHECK ("action" IN ('open', 'close')),
    fired_on TIMESTAMPTZ NOT NULL,
    created_on TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_on TIMESTAMPTZ NOT NULL DEFAULT NOW()
);