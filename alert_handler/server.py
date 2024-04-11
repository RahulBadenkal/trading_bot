import json
import logging
import os
from datetime import datetime
from typing import Any, List

import httpx
from fastapi_utils.tasks import repeat_every
from queue import Queue

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel

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
    name: str
    job: str


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
        # Log the error, send it to an error tracking system, etc.
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
async def execute_trade(alert: AlertRequest):
    try:
        data = alert.dict()
        response = await exchange_client.post("/api/users", json=data, timeout=5)
        httpx_raise_for_status(response)

        logging.info(response.json())
    except Exception as e:
        logging.error(get_stack_trace(e))


async def save_to_db():
    try:
        logging.info(f"save to db callback. alert queue size: {alert_queue.qsize()}")

        alerts: List[AlertRequest] = []
        for _ in range(Config.db_max_batch_size):
            if not alert_queue.empty():
                alerts.append(alert_queue.get())
                alert_queue.task_done()
            else:
                break
        if len(alerts) == 0:
            return

        # Save to db
        async with Config.pool.acquire() as db_connection:
            await db_connection.executemany('''
                INSERT INTO alert (name, job, created_on, updated_on)
                VALUES ($1, $2, NOW(), NOW())
            ''', [
                (
                    row.name,
                    row.job,
                ) for row in alerts
            ])
        logging.info(f"saved: {len(alerts)} to db")

    except Exception as e:
        logging.error(get_stack_trace(e))


##########
# Routes #
##########
@app.get("/health")
async def health():
    return {"message": "Server is up"}


@app.post("/alert")
async def load(alert: AlertRequest, background_tasks: BackgroundTasks):
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
