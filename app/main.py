from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.routes.loan_transaction import router as loan_transaction_router
from app.routes import auth, user, userRoles, company, loan, bank, document, history, alert, sms, transaction
from app.database import engine, Base
import logging
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from app.routes import loan_transaction
import app.models as models
# Avoid connecting to the DB at import time; run migrations on startup instead.
#Base.metadata.drop_all(bind=engine)   # Deletes all tables


app = FastAPI(title="RestoreLoans API2", version="1.0.0")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    content_type = request.headers.get("content-type", "<none>")
    received_keys = None
    try:
        form = await request.form()
        received_keys = list(form.keys())
    except Exception:
        pass
    if not received_keys:
        try:
            body = await request.json()
            if isinstance(body, dict):
                received_keys = list(body.keys())
        except Exception:
            received_keys = None
    logging.error(
        "422 Validation error on %s %s | content-type=%s | keys received=%s | errors=%s",
        request.method, request.url.path, content_type, received_keys,
        [(e.get("loc"), e.get("msg")) for e in errors])
    return JSONResponse(status_code=422, content={"detail": errors})


@app.on_event("startup")
async def startup_event():
    try:
        # Run blocking DB schema creation in a thread to avoid blocking the event loop
        await asyncio.to_thread(Base.metadata.create_all, bind=engine)
    except Exception as e:
        logging.error("Database unavailable on startup: %s", e)
        # don't re-raise so the app can still start if DB is temporarily unreachable
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