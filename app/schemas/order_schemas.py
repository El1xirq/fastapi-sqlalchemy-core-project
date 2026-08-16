from pydantic import BaseModel, EmailStr
from typing import List
from datetime import datetime


class OrderSchema(BaseModel):
    pass

class OrderItemCreateSchema(OrderSchema):
    product_id: int
    quantity: int


class OrderCreateSchema(BaseModel):
    user_id: int
    items: List[OrderItemCreateSchema]


class OrderResponseSchema(OrderSchema):
    id: int
    user_id: int
    total: float
    created_at: datetime


class OrderUsersSchema(OrderResponseSchema):
    name: str
    email: EmailStr
    age: int


class OrderStatsSchema(OrderSchema):
    user_id: int
    user_name: str
    orders_count: int
    total_sum: float
    avg_total: float