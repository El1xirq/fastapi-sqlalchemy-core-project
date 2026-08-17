from fastapi import APIRouter, status, HTTPException
from app.schemas.order_schemas import OrderResponseSchema, OrderCreateSchema, OrderUsersSchema, OrderStatsSchema, OrderListSchema
from sqlalchemy import select, insert, func, delete, update
from app.models import products, orders, order_item, users
from app.database import get_connection
from sqlalchemy.exc import SQLAlchemyError
from typing import List


router = APIRouter(prefix='/orders', tags=['orders'])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=OrderResponseSchema)
async def post_order(order: OrderCreateSchema):
    try:
        product_ids = [item.product_id for item in order.items]
        stmt = select(products.c.id, products.c.price, products.c.stock).where(products.c.id.in_(product_ids)).with_for_update()
        
        async with get_connection() as conn:
            result = await conn.execute(stmt)
            product_prices = {row.id: row for row in result.fetchall()}
            
            if len(product_prices) != len(product_ids):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Some products not found")
            
            total = 0
            for item in order.items:
                if item.product_id not in product_prices:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {item.product_id} not found")
                
                product = product_prices[item.product_id]
                if product.stock < item.quantity:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not enough stock for product {item.product_id}")
                    
                total += product.price * item.quantity
            
            stmt = (
                insert(orders)
                .values(user_id=order.user_id, total=total)
                .returning(orders.c.id, orders.c.user_id, orders.c.total, orders.c.created_at)
            )
            result = await conn.execute(stmt)
            new_order = result.fetchone()
            
            for item in order.items:
                stmt_update = (
                    update(products)
                    .where(products.c.id == item.product_id)
                    .values(stock=products.c.stock - item.quantity)
                )
                await conn.execute(stmt_update)

                stmt = insert(order_item).values(
                    order_id=new_order.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price_at_time=product_prices[item.product_id].price
                )
                await conn.execute(stmt)
                
                return {
                    "id": new_order.id,
                    "user_id": new_order.user_id,
                    "total": new_order.total,
                    "created_at": new_order.created_at,
                    "items": [
                        {
                            "product_id": item.product_id,
                            "quantity": item.quantity,
                            "price_at_time": float(product_prices[item.product_id].price)
                        }
                        for item in order.items]}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        print(f"Ошибка при создании: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)



@router.get('/with-users', status_code=status.HTTP_200_OK, response_model=List[OrderUsersSchema])
async def get_order_with_users():
    """Присоедение USERS к ORDERS, INNER JOIN"""
    stmt = select(orders, users).join(users, orders.c.user_id == users.c.id)
    async with get_connection() as conn:
        result = await conn.execute(stmt)
        return result.mappings().all()


@router.get('/stats', status_code=status.HTTP_200_OK, response_model=List[OrderStatsSchema])
async def get_stats_orders(min_orders: int = 0):
    """Получение статистики ORDERS, COUNT, SUM, TOTAL"""
    subq = (select(orders.c.user_id, func.count(orders.c.id).label('orders_count'),
                  func.sum(orders.c.total).label('total_sum'),
                  func.avg(orders.c.total).label('avg_total'))
                  .having(func.count(orders.c.id) > min_orders)
                  .group_by(orders.c.user_id).cte())

    stmt = (select(users.c.id.label('user_id'), 
                   users.c.name.label('user_name'),
                    func.coalesce(subq.c.orders_count, 0).label('orders_count'),
                    func.coalesce(subq.c.total_sum, 0).label('total_sum'),
                    func.coalesce(subq.c.avg_total, 0).label('avg_total'))
                    .select_from(users.join(subq, users.c.id == subq.c.user_id))
                    .order_by(subq.c.orders_count.desc()))

    async with get_connection() as conn:
        result = await conn.execute(stmt)
        return result.mappings().all()


@router.get('/', status_code=status.HTTP_200_OK, response_model=List[OrderListSchema])
async def get_orders():
    """Получение всех заказов"""
    stmt = select(orders)
    async with get_connection() as conn:
        result = await conn.execute(stmt)
        return result.mappings().all()


@router.get('/{id}', status_code=status.HTTP_200_OK, response_model=OrderListSchema)
async def get_order_id(id: int):
    """Получение заказа по ID"""
    stmt = select(orders).where(orders.c.id == id)
    async with get_connection() as conn:
        result = await conn.execute(stmt)
        order = result.mappings().one_or_none()

        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Order with this ID({id}) not found')

        return order

        
@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_order_id(id: int):
    """Удаление заказа по ID"""
    check_query = select(orders).where(orders.c.id == id)
    stmt = delete(orders).where(orders.c.id == id)
    stmt_order_item = delete(order_item).where(order_item.c.order_id == id)
    async with get_connection() as conn:
        result_query = await conn.execute(check_query)
        order = result_query.mappings().one_or_none()

        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Order with this ID({id}) not found')
        
        await conn.execute(stmt_order_item)
        await conn.execute(stmt)
        return None

        

