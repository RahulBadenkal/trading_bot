CREATE OR REPLACE PROCEDURE upsert_trade(trades trade_type[])
LANGUAGE plpgsql AS $$
DECLARE
    r trade_type;
    max_fired_on TIMESTAMPTZ;
BEGIN
    FOREACH r IN ARRAY trades
    LOOP
        -- Retrieve the latest fired_on date for the current coin
        SELECT MAX(fired_on) INTO max_fired_on FROM trade WHERE coin = r.coin;

        -- Proceed if the new fired_on is greater than the existing max_fired_on or if no record exists (max_fired_on is NULL)
        IF max_fired_on IS NULL OR r.fired_on > max_fired_on THEN
            IF r.status = 'open' THEN
                -- Insert a new record for 'open' status, ignoring conflicts with unique constraints
                INSERT INTO trade (id, alert_id, coin, status, fired_on, created_on, updated_on)
                VALUES (r.id, r.alert_id, r.coin, r.status, r.fired_on, NOW(), NOW())
                ON CONFLICT (coin) WHERE status = 'open' DO NOTHING;
            ELSIF r.status = 'close' THEN
                -- Update the record to 'close' status if the existing status is 'open'
                UPDATE trade
                SET status = 'close',
                    fired_on = r.fired_on,
                    updated_on = NOW()
                WHERE coin = r.coin AND status = 'open';
            END IF;
        END IF;
    END LOOP;
END;
$$;
