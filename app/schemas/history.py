from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class StatementHistoryBase(BaseModel):
    user_id: int
    loan_id: Optional[int]  # Loan ID is optional
    statement_type: str  # 'application' or 'financial'
    file_path: str

class StatementHistoryCreate(StatementHistoryBase):
    pass  # Inherits all fields from StatementHistoryBase for creation

class StatementHistoryResponse(StatementHistoryBase):
    id: int
    statement_date: datetime  # Automatically set by the database

    class Config:
        orm_mode = True