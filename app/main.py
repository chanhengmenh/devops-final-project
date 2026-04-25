from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from typing import List

app = FastAPI(title="FoodExpress Learning Platform API")

Instrumentator().instrument(app).expose(app)

orders_db: List[dict] = []


class Order(BaseModel):
    item: str
    quantity: int
    price: float


@app.get("/")
def root():
    return {"message": "FoodExpress Learning Platform API v2"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/orders")
def get_orders():
    return {"orders": orders_db}


@app.post("/orders")
def create_order(order: Order):
    entry = {"id": len(orders_db) + 1, **order.dict()}
    orders_db.append(entry)
    return entry


@app.get("/grades")
def get_grades():
    return {"grades": [{"student": "Alice", "score": 95}, {"student": "Bob", "score": 82}]}
