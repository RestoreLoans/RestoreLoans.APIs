from fastapi import FastAPI
from app.routes.loan_transaction import router as loan_transaction_router
from app.routes import auth, user, userRoles, company, loan, bank, document, history, alert, sms, transaction
from app.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from app.routes import loan_transaction
import app.models as models
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RestoreLoans API2", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(loan_transaction.router)
app.include_router(user.router)
app.include_router(userRoles.router)
app.include_router(company.router)
app.include_router(loan.router)
app.include_router(bank.router)
app.include_router(document.router)
app.include_router(history.router)
app.include_router(alert.router)
app.include_router(sms.router)
app.include_router(transaction.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to RestoreLoans API"}