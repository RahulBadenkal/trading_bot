CREATE TABLE trade (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_id UUID REFERENCES alert(id),
    coin VARCHAR NOT NULL,
    status VARCHAR NOT NULL CHECK (status IN ('open', 'close')),
    fired_on TIMESTAMPTZ NOT NULL,
    created_on TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_on TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX trade_unique_coin_when_open ON trade(coin) WHERE status = 'open';
CREATE INDEX trade_coin_fired_on ON trade (coin, fired_on DESC);