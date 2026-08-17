from pydantic import BaseModel
from typing import List
from datetime import datetime


class OrderListSchema(BaseModel):
    id: int
    user_id: int
    total: float
    created_at: datetime


class OrderItemCreateSchema(BaseModel):
    product_id: int
    quantity: int


class OrderItemResponseSchema(BaseModel):
    product_id: int
    quantity: int
    price_at_time: float


class OrderCreateSchema(BaseModel):
    user_id: int
    items: List[OrderItemCreateSchema]


class OrderResponseSchema(BaseModel):
    id: int
    user_id: int
    total: float
    created_at: datetime
    items: List[OrderItemResponseSchema]


class OrderUsersSchema(BaseModel):
    id: int
    user_id: int
    total: float
    created_at: datetime
    name: str
    email: str
    age: int


class OrderStatsSchema(BaseModel):
    user_id: int
    user_name: str
    orders_count: int
    total_sum: float
    avg_total: float