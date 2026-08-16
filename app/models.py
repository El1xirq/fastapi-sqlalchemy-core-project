from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime, ForeignKey, Boolean, Float, Numeric
from sqlalchemy.sql import func
from .database import metadata



users = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String(100), nullable=False),
    Column('email', String(100), nullable=False, unique=True),
    Column('age', Integer),
    Column('created_at', DateTime, server_default=func.now())
)


products = Table(
    'products',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String(200), nullable=False),
    Column('price', Numeric(10, 2), nullable=False),
    Column('stock', Integer, default= 0, nullable=False),
    Column('category', String(100), nullable=False)
)


orders = Table(
    'orders',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('total', Numeric(10, 2), nullable=False),
    Column('created_at', DateTime, server_default=func.now())
)


order_item = Table(
    'order_items',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('order_id', Integer, ForeignKey('orders.id')),
    Column('product_id', Integer, ForeignKey('products.id')),
    Column('quantity', Integer, nullable=False),
    Column('price_at_time', Float, nullable=False),
)

