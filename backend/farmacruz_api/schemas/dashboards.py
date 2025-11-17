from pydantic import BaseModel, Field
from typing import List, Optional

class DashboardStats(BaseModel):
    total_users: int
    total_products: int
    total_orders: int
    pending_orders: int
    total_revenue: float
    low_stock_count: int
    total_customers: int
    total_sellers: int

class SalesReportItem(BaseModel):
    order_id: int
    customer_name: str
    customer_email: str
    order_date: str
    status: str
    total_amount: float
    items_count: int

class SalesReport(BaseModel):
    start_date: str
    end_date: str
    total_orders: int
    total_revenue: float
    orders: List[SalesReportItem]