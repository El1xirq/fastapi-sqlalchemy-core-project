from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any

class ProductSchema(BaseModel):
    pass


class ProductReponseSchema(ProductSchema):
    id: int
    name: str
    price: float
    stock: int
    category: str


class ProductCreateSchema(ProductSchema):
    name: str = Field(max_length=200)
    price: float
    stock: int = Field(default=0)
    category: str = Field(max_length=100)

    @field_validator('name', 'category', mode='before')
    @classmethod
    def capitalize_fields(cls, v: Any) -> Any:
        if isinstance(v, str) and v:
            return v.capitalize()
        return v


class ProductPatchSchema(ProductSchema):
    name: Optional[str]
    price: Optional[float]
    stock: Optional[int]
    category: Optional[str]


    @field_validator('name', 'category', mode='before')
    @classmethod
    def capitalize_fields(cls, v: Any) -> Any:
        if isinstance(v, str) and v:
            return v.capitalize()
        return v
