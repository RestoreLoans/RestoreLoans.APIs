from pydantic import BaseModel
from typing import Optional

class StatementHistoryCreate(BaseModel):
    user_id: int
    loan_id: int
    statement_type: str
    file_path: str

class StatementHistoryResponse(BaseModel):
    id: int
    user_id: int
    loan_id: int
    statement_type: str
    file_path: str

    class Config:
        from_attributes= True

class StatementHistoryUpdate(BaseModel):
    statement_type: Optional[str] = None
    file_path: Optional[str] = None