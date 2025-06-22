from fastapi import FastAPI
from app.routes import auth, user, userRoles, loan, bank, document, history, alert, sms, transaction, company
from app.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RestoreLoans API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (⚠️ Not safe for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
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