from pydantic import BaseModel
from datetime import date

class HistoryBase(BaseModel):
    statement_type: str
    file_path: str

class HistoryResponse(HistoryBase):
    id: int
    user_id: int
    loan_id: int = None
    statement_date: date

    class Config:
        orm_mode = True