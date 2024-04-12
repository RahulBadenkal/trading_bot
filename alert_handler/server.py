import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, List, Literal, Union, Dict

import httpx
from fastapi_utils.tasks import repeat_every
from queue import Queue

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, validator

from alert_handler.config import Config
from common.httpx_utils import httpx_raise_for_status
from common.utils import get_stack_trace

app = FastAPI()
templates: Jinja2Templates = None


####################
# Global variables #
####################
alert_queue = Queue()
exchange_client = httpx.AsyncClient(base_url="https://reqres.in")  # This ensures reusing connections for future calls


#########
# Types #
#########
class AlertRequest(BaseModel):
    coin: str
    action: Literal["open", "close"]


############
# Handlers #
############
@app.on_event("startup")
async def startup_event():
    global templates

    await Config.init()

    app.mount("/static", StaticFiles(directory=os.path.join(Config.project_dir_path, 'alert_handler', 'static')),
              name="static")
    templates = Jinja2Templates(directory=os.path.join(Config.project_dir_path, 'alert_handler', 'templates'))


@app.on_event("startup")
@repeat_every(seconds=10, wait_first=True)
async def save_to_db_interval():
    await save_to_db()


@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        stack_trace = get_stack_trace(e)
        logging.error(stack_trace)
        error_response = {
            "errorCode": 500,
            "errorMessage": str(e),
            "stackTrace": stack_trace
        }
        return JSONResponse(content=error_response, status_code=500)


###########
# Helpers #
###########
async def execute_trade(alert: Any):
    try:
        response = await exchange_client.post("/api/users", json={"name": "heyo", "job": "Detective"}, timeout=5)
        httpx_raise_for_status(response)

        logging.info(response.json())
    except Exception as e:
        # exceptions don't automatically get logged, so need to do that manually
        logging.error(get_stack_trace(e))


async def save_to_db():
    try:
        logging.info(f"save to db callback. alert queue size: {alert_queue.qsize()}")

        alerts: List[Any] = []
        trades: List[Any] = []
        for _ in range(Config.db_max_batch_size):
            if not alert_queue.empty():
                new_alert = alert_queue.get()
                alert_queue.task_done()

                new_alert["id"] = uuid.uuid4()
                alerts.append(new_alert)

                trades.append({
                    "id": uuid.uuid4(),
                    "alert_id": new_alert["id"],
                    "coin": new_alert["coin"],
                    "status": new_alert["action"],
                    "fired_on": new_alert['fired_on'],
                })
            else:
                break
        if len(alerts) == 0:
            return

        # Save to db
        async with Config.pool.acquire() as db_connection:
            # Save alerts table
            await db_connection.executemany('''
                INSERT INTO alert (id, coin, action, fired_on, created_on, updated_on)
                VALUES ($1, $2, $3, $4, NOW(), NOW())
            ''', [
                (
                    row['id'],
                    row['coin'],
                    row['action'],
                    row['fired_on'],
                ) for row in alerts
            ])

            # Save trades table
            trades = [
                (row['id'], row['alert_id'], row['coin'], row['status'], row['fired_on'])
                for row in trades
            ]
            await db_connection.execute(
                "CALL upsert_trade($1::trade_type[])",
                (trades,)
            )
        logging.info(f"saved: {len(alerts)} to db")

    except Exception as e:
        # exceptions don't automatically get logged, so need to do that manually
        logging.error(get_stack_trace(e))


##########
# Routes #
##########
@app.get("/health")
async def health():
    return {"message": "Server is up"}


@app.post("/alert")
async def load(alert: AlertRequest, background_tasks: BackgroundTasks):
    alert = alert.dict()
    alert['fired_on'] = datetime.now()  # Need a field that indicated which is the latest alert
    alert_queue.put(alert)
    background_tasks.add_task(execute_trade, alert=alert)

    return {
        "message": "Request received"
    }


# @app.get("/calculator", response_class=HTMLResponse)
# async def calculator(request: Request):
#     with open("data.json") as f:
#         data = json.load(f)
#     # data = await calculator_controller()
#     # with open("data.json", "w") as f:
#     #     json.dump(data, f)
#     return templates.TemplateResponse("index.html", {
#         "request": request,
#         "title": "Calculator",
#         "data": data
#     })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)
