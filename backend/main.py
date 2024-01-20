from fastapi import *
from fastapi.routing import APIRouter
from pydantic import BaseModel, field_validator
from reportlab.pdfgen import canvas
from sqlalchemy import *
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID 
import settings
import uuid
import re
import uvicorn
from typing import *
from starlette.responses import FileResponse
import ormar
from fpdf import FPDF
from auth import *
from deta import Deta



# подключение к бд
engine = create_async_engine(settings.REAL_DATABASE_URL, future=True, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

async def get_db() -> Generator:
    try:
        session: AsyncSession = async_session()
        yield session
    finally:
        await session.close()


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)


class UserDAL:
    """инфа о пользователе"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def create_user(
        self, name: str
    ) -> User:
        new_user = User(
            name = name
        )
        self.db_session.add(new_user)
        await self.db_session.flush()
        return new_user


LETTER_MATCH_PATTERN = re.compile(r"^[а-яА-Яa-zA-Z\-]+$")

# Модели данных

class TunedModel(BaseModel):
    class Config:
        """конвертирование пандантик в джсон"""
        from_attributes = True


class UserCreate(BaseModel):
    name: str
    @field_validator("name")
    def validator_name(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Name should contains only letters"
            )
        return value


class ShowUser(TunedModel):
    user_id: uuid.UUID
    name: str
    is_active: bool


class Employee(BaseModel):    
    id: uuid.UUID
    name: str
    position: str

    @field_validator("name")
    def validator_name(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Name should contains only letters"
            )
        return value


class Visitor(BaseModel):
    id: uuid.UUID
    name: str
    phone: str

    @field_validator("name")
    def validator_name(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Name should contains only letters"
            )
        return value


class LoyaltyCard(BaseModel):
    id: uuid.UUID
    visitor_id: int
    points: int


class Order(BaseModel):
    id: uuid.UUID
    visitor_id: int
    items: str


# class Doc(BaseModel):
#     title: str
#     text: str
#     author: str


class OrderOut(Order):
    id: uuid.UUID


# Хэш-таблицы для хранения данных
employees = {}
visitors = {}
loyalty_cards = {}
orders = {}


app = FastAPI(title="Small Shmel")
client = None
# CRUD методы для сущностей

# Сотрудники
@app.get("/employees")
async def get_employees():
    return employees.values()

@app.get("/employees/{employee_id}")
async def get_employee(employee_id: int):
    return employees.get(employee_id)

@app.post("/employees")
async def create_employee(employee: Employee):
    employees[employee.id] = employee
    return employee

@app.put("/employees/{employee_id}")
async def update_employee(employee_id: int, employee: Employee):
    if employee_id in employees:
        employees[employee_id] = employee
        return employee

@app.delete("/employees/{employee_id}")
async def delete_employee(employee_id: int):
    if employee_id in employees:
        del employees[employee_id]

# Посетители
@app.get("/visitors")
async def get_visitors():
    return visitors.values()

@app.get("/visitors/{visitor_id}")
async def get_visitor(visitor_id: int):
    return visitors.get(visitor_id)

@app.post("/visitors")
async def create_visitor(visitor: Visitor):
    visitors[visitor.id] = visitor
    return visitor

@app.put("/visitors/{visitor_id}")
async def update_visitor(visitor_id: int, visitor: Visitor):
    if visitor_id in visitors:
        visitors[visitor_id] = visitor
        return visitor

@app.delete("/visitors/{visitor_id}")
async def delete_visitor(visitor_id: int):
    if visitor_id in visitors:
        del visitors[visitor_id]

# Карты лояльности
@app.get("/loyalty_cards")
async def get_loyalty_cards():
    return loyalty_cards.values()

@app.get("/loyalty_cards/{card_id}")
async def get_loyalty_card(card_id: int):
    return loyalty_cards.get(card_id)

@app.post("/loyalty_cards")
async def create_loyalty_card(card: LoyaltyCard):
    loyalty_cards[card.id] = card
    return card

@app.put("/loyalty_cards/{card_id}")
async def update_loyalty_card(card_id: int, card: LoyaltyCard):
    if card_id in loyalty_cards:
        loyalty_cards[card_id] = card
        return card

@app.delete("/loyalty_cards/{card_id}")
async def delete_loyalty_card(card_id: int):
    if card_id in loyalty_cards:
        del loyalty_cards[card_id]

# Заказы
@app.get("/orders")
async def get_orders():
    return orders.values()

@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    return orders.get(order_id)

@app.post("/orders")
async def create_order(order: Order):
    orders[order.id] = order
    return order

@app.put("/orders/{order_id}")
async def update_order(order_id: int, order: Order):
    if order_id in orders:
        orders[order_id] = order
        return order

@app.delete("/orders/{order_id}")
async def delete_order(order_id: int):
    if order_id in orders:
        del orders[order_id]

# Генерация чеков

pdf = APIRouter()

class PDF(FPDF):
    def titles(self, title):
        self.set_xy(0.0, 0.0)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(220, 50, 50)
        self.cell(w=210.0, h=40.0, align='C', txt=title, border=0)

    def texts(self, text):
        self.set_xy(10.0, 40.0)
        self.set_text_color(76.0, 32.0, 250.0)
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, text)


async def create_order(order: Order) -> Order:
    return await Order.objects.create(**order.dict())

async def create_pdf(pk: int) -> str:
    try:
        _order = await Order.objects.get(id=pk)
    except ormar.exceptions.NoMatch:
        raise HTTPException(status_code=404, detail="Not found")
    
    path = f'static/{_order.title}.pdf'
    _pdf = PDF()
    _pdf.add_page()
    _pdf.titles(_order.title)
    _pdf.texts(_order.text)
    _pdf.set_author(_order.author)
    _pdf.output(path, 'F')


@pdf.post('/check', response_model=OrderOut)
async def generate_pdf_check(order: Order):
    # pdf_filename = f"check_{order.id}.pdf"
    # c = canvas.Canvas(pdf_filename)
    return await create_order(order)

@pdf.get('/check{pk}')
async def pdf_check(pk: int):
    return FileResponse(await create_pdf(pk))

# @app.post("/generate_check/{order_id}")
# async def generate_check(order_id: int):
#     order = orders.get(order_id)
#     pdf_filename = generate_pdf_check(order)
#     return {"pdf_filename": pdf_filename}


#маршрутиризация
user_router = APIRouter()

async def _create_new_user(body: UserCreate) -> ShowUser:
    async with async_session() as session:
        async with session.begin():
            user_dal = UserDAL(session)
            user = await user_dal.create_user(
                name=body.name,
            )
            return ShowUser(
                user_id=user.user_id,
                name=user.name,
                is_active=user.is_active,
            )
        

@user_router.post("/", response_model=ShowUser)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)) -> ShowUser:
    return await _create_new_user(body, db)

main_api_router = APIRouter()

main_api_router.include_router(user_router, prefix="/user", tags=["user"])
app.include_router(main_api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

