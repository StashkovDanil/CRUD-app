"""
Pydantic-схемы запросов/ответов API.
Структура один в один повторяет components/schemas из api/openapi.yaml —
контракт был спроектирован первым (API First), код лишь его реализует.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------- Категории
class CategoryIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None


class CategoryOut(CategoryIn):
    id: int


# --------------------------------------------------------------- Поставщики
class SupplierIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    contact_person: Optional[str] = Field(None, max_length=150)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=150)


class SupplierOut(SupplierIn):
    id: int


# ------------------------------------------------------------------ Склады
class WarehouseIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    address: Optional[str] = Field(None, max_length=255)


class WarehouseOut(WarehouseIn):
    id: int


# ------------------------------------------------------------------ Товары
class ProductIn(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    category_id: int
    unit: Optional[str] = Field(None, max_length=20, description="По умолчанию 'шт'")
    price: Decimal = Field(0, ge=0)
    description: Optional[str] = None


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    category_id: int
    unit: str
    price: Decimal
    description: Optional[str] = None


class ProductWithCategory(ProductOut):
    category_name: str


# ------------------------ Остатки: M:M products <-> warehouses (+ quantity)
class StockOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    warehouse_id: int
    warehouse_name: str
    quantity: Decimal
    updated_at: datetime


class StockAdjust(BaseModel):
    quantity: Decimal = Field(..., ge=0)


# --------------- Документы: M:M documents <-> products (+ quantity, price)
class DocumentItemIn(BaseModel):
    product_id: int
    quantity: Decimal = Field(..., gt=0)
    price: Decimal = Field(0, ge=0)


class DocumentItemOut(DocumentItemIn):
    id: int
    product_name: str


class DocumentIn(BaseModel):
    doc_number: str = Field(..., min_length=1, max_length=50)
    doc_type: Literal["IN", "OUT"]
    warehouse_id: int
    supplier_id: Optional[int] = None
    comment: Optional[str] = None
    items: List[DocumentItemIn] = Field(..., min_length=1)


class DocumentOut(BaseModel):
    id: int
    doc_number: str
    doc_type: str
    warehouse_id: int
    warehouse_name: str
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    status: str
    created_at: datetime
    comment: Optional[str] = None


class DocumentDetail(DocumentOut):
    items: List[DocumentItemOut]