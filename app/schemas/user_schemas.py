from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime



class UserSchema(BaseModel):
    pass

class UserSchemaPost(UserSchema):
    name: str
    email: EmailStr
    age: int = Field(ge=1, le=100)

    @field_validator('name', mode='before')
    @classmethod
    def capitalize_name(cls, v):
        if isinstance(v, str) and v:
            return v[0].upper() + v[1:]
        return v

class UserSchemaResponse(UserSchema):
    id: int
    name: str
    email: EmailStr
    age: int
    created_at: datetime


class UserSchemaName(UserSchema):
    name: str

class UserOrdersSchema(UserSchemaResponse):
    order_id: int
    total: float


class UserStatsSchema(UserSchemaResponse):
    orders_count: int
    orders_sum: float
    orders_avg: float
    orders_min: float


class UserFormattedSchema(UserSchemaResponse):
    email_upper: str
    name_length: int
    email_domain: str


class UserTopSchema(UserSchema):
    id: int
    name: str
    email: EmailStr
    total_spent: float









