from fastapi import APIRouter, status, HTTPException
from app.schemas.user_schemas import UserSchemaPost, UserSchemaResponse, UserSchemaName, UserOrdersSchema, UserStatsSchema, UserFormattedSchema
from app.database import get_connection
from sqlalchemy import insert, select, func, update, delete
from app.models import users, orders
from typing import List
from sqlalchemy.exc import SQLAlchemyError



router = APIRouter(prefix='/users', tags=['users'])


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=UserSchemaResponse)
async def user_post(user: UserSchemaPost):
    """Создания пользователя"""
    try:
        async with get_connection() as conn:
            query = select(users).where(users.c.email == user.email)
            result_query = (await conn.execute(query)).fetchall()
            if len(result_query) > 0:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'This email({user.email}) is busy')

            
            stmt = insert(users).values(name = user.name, email= user.email, age=user.age).returning(users)
            result = await conn.execute(stmt)
            row = result.fetchone()
            return row._asdict()
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        print(f"Ошибка при создании: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post('/bulk', status_code=status.HTTP_201_CREATED, response_model=List[UserSchemaResponse])
async def users_post_bulk(users_data: List[UserSchemaPost]):
    """Создание пользователей, множественная вставка"""
    try:
        if not users_data:
            return []
        
        incoming_emails = [user.email for user in users_data]
        if len(incoming_emails) != len(set(incoming_emails)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="There are duplicate emails in the sent list"
            )

        payload = [user.model_dump() for user in users_data]
        stmt = insert(users).values(payload).returning(users)
        
        async with get_connection() as conn:
            query = select(users).where(users.c.email.in_(incoming_emails))
            existing_users = (await conn.execute(query)).fetchall()
            if len(existing_users) > 0:
                existing_emails = {row.email for row in existing_users}
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, 
                    detail=f"This email is busy: {list(existing_emails)}"
                )


            result = await conn.execute(stmt)
            return [row._asdict() for row in result.fetchall()]
    except HTTPException:
        raise
    except SQLAlchemyError as e:
            print(f"Ошибка при создании: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get('/', status_code=status.HTTP_200_OK, response_model=List[UserSchemaResponse])
async def get_users():
    """Получение всех пользователей"""
    query = select(users).order_by(users.c.id)

    async with get_connection() as conn:
        result = await conn.execute(query)
        return result.mappings().all()


@router.get('/names', status_code=status.HTTP_200_OK, response_model=List[UserSchemaName])
async def get_name_users():
    """Получение имен пользователей"""
    query = select(users.c.name)

    async with get_connection() as conn:
        result = await conn.execute(query)
        return result.mappings().all()


@router.get('/filter/', status_code=status.HTTP_200_OK, response_model=List[UserSchemaResponse])
async def get_user_filter(
    age: int | None = None,          
    age_min: int | None = None,       
    age_max: int | None = None,       
    name: str | None = None,          
    email_domain: str | None = None,  
    ids: str | None = None,
    limit: int | None = None,
    offset: int | None = None):
    """Получение пользователей с учетом фильтрации"""

    conditions = []

    async with get_connection() as conn:
        stmt = select(users)
        
        if age is not None:
            conditions.append(users.c.age == age)

        if age_min is not None and age_max is not None:
            conditions.append(users.c.age.between(age_min, age_max))
        else:
            if age_min is not None:
                    conditions.append(users.c.age >= age_min)
            if age_max is not None:
                    conditions.append(users.c.age <= age_max)

        if name is not None:
            conditions.append(users.c.name.like(f'%{name}%'))

        if email_domain is not None:
            conditions.append(users.c.email.like(f'%@{email_domain}%'))

        if ids is not None:
            ids_list = [int(x.strip()) for x in ids.split(',')]
            conditions.append(users.c.id.in_(ids_list))


        if conditions:
            stmt = stmt.where(*conditions)

        if limit is not None:
            stmt = stmt.limit(limit)

        if offset is not None:
            stmt = stmt.offset(offset)

        result = await conn.execute(stmt)
        return result.mappings().all()


@router.get('/with-orders', status_code=status.HTTP_200_OK, response_model=List[UserOrdersSchema])
async def get_user_orders_join():
    """Присоедение ORDERS к USERS"""
    stmt = select(users).join(orders, users.c.id == orders.c.user_id)

    async with get_connection() as conn:
        result = await conn.execute(stmt)
        return result.mappings().all()


@router.get('/sorted', status_code=status.HTTP_200_OK, response_model=List[UserSchemaResponse])
async def get_user_sorted(
    sort_by: str | None = None, 
    order: str | None = None
):
    """SORTED USER ASC, DESC, Column"""
    valid_fields = ['id', 'name', 'email', 'age', 'created_at']

    stmt = select(users)
    
    if sort_by is not None:
        if sort_by not in valid_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sort field. Allowed: {', '.join(valid_fields)}"
            )
        
        if order is None or order.upper() == 'ASC':
            stmt = stmt.order_by(getattr(users.c, sort_by).asc())
        elif order.upper() == 'DESC':
            stmt = stmt.order_by(getattr(users.c, sort_by).desc())
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must be 'ASC' or 'DESC'"
            )
    else:
        stmt = stmt.order_by(users.c.id.asc())
    
    async with get_connection() as conn:
        result = await conn.execute(stmt)
        rows = result.mappings().all()
        return rows


@router.get('/top-spenders', status_code = status.HTTP_200_OK, response_model=List[UserSchemaResponse])
async def get_user_top_spenders(value: int | None = 0):
    """Получение пользователей, где общая сумма больше value"""

    if value < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Value({value}) must be 0')

    subquery = select(orders.c.user_id, func.sum(orders.c.total).label('total_spent')).group_by(orders.c.user_id)
    subquery = subquery.having(func.sum(orders.c.total) > value)
    stmt = (select(
        users.c.id,
        users.c.name,
        users.c.email,
        subquery.c.total_spent)
        .select_from(users.join(subquery, users.c.id == subquery.c.user_id))
        .order_by(subquery.c.total_spent.desc()))

    async with get_connection() as conn:
        result = await conn.execute(stmt)
        return result.mappings().all()


@router.get('/hierarchy', status_code=status.HTTP_200_OK, response_model=List[UserStatsSchema])
async def get_users_stats():
    """Получение статистики пользователе, AVG, SUM, MIN, COUNT"""
    subq = (select(orders.c.user_id, func.count(orders.c.user_id).label('orders_count'),
                  func.sum(orders.c.total).label('orders_sum'),
                  func.avg(orders.c.total).label('orders_avg'),
                  func.min(orders.c.total).label('orders_min'))
                  .group_by(orders.c.user_id).cte())

    stmt = (select(users.c.id, users.c.name, users.c.email, users.c.age, users.c.created_at,
                    func.coalesce(subq.c.orders_count, 0).label('orders_count'),
                    func.coalesce(subq.c.orders_sum, 0).label('orders_sum'),
                    func.coalesce(subq.c.orders_avg, 0).label('orders_avg'),
                    func.coalesce(subq.c.orders_min, 0).label('orders_min'))
            .join(subq, users.c.id == subq.c.user_id, isouter=True)
            .order_by(users.c.id))


    async with get_connection() as conn:
        result = await conn.execute(stmt)
        return result.mappings().all()
    

@router.get('/formatted', status_code=status.HTTP_200_OK, response_model=List[UserFormattedSchema])
async def formatted_users():
    """Получение пользователей с форматированием, UPPER, CHAR_LENGTH, SUBSTRING"""
    stmt = select(users.c.id, users.c.name, users.c.email, users.c.age, users.c.created_at,
                   func.upper(users.c.email).label('email_upper'),
                   func.char_length(users.c.name).label('name_length'),
                   func.substring(users.c.email, func.strpos(users.c.email, '@') + 1).label('email_domain')).order_by(users.c.id)

    async with get_connection() as conn:
        result = await conn.execute(stmt)
        return result.mappings().all()


@router.get('/{id}', status_code=status.HTTP_200_OK, response_model=UserSchemaResponse)
async def get_user_id(id: int):
    """Получение пользователя по ID"""
    stmt = select(users).where(users.c.id==id)
    async with get_connection() as conn:
        result = await conn.execute(stmt)
        user = result.mappings().first()

        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with this ID({id}) not found')

        return user


@router.put("/{id}", status_code=status.HTTP_200_OK, response_model=UserSchemaResponse)
async def put_user_id(id: int, user_data: UserSchemaPost):
    """Изменения пользователя по ID"""
    check_query = select(users).where(users.c.id == id)

    stmt = update(users).where(users.c.id == id).values(name = user_data.name, age = user_data.age, email = user_data.email).returning(users)

    async with get_connection() as conn:
        check_result = await conn.execute(check_query)
        exists = check_result.one_or_none()

        if exists is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User ID({id} not found.)")

        result = await conn.execute(stmt)
        row = result.fetchone()
        return row._asdict()


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_id(id: int):
    """Удаление пользователя по ID"""
    check_query = select(users).where(users.c.id == id)
    stmt = delete(users).where(users.c.id == id)
    
    async with get_connection() as conn:
        check_result = await conn.execute(check_query)
        exists = check_result.one_or_none()
    
        if exists is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User ID({id} not found.)")

        await conn.execute(stmt)
        return None


