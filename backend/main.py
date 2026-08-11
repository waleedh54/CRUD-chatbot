import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

import models, schemas, crud, auth
from database import engine, get_db
from nlu import intent_handler

load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Admin Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def seed_admins():
    """Seeds allowed admin emails from .env so they can auto-login."""
    admin_emails = os.getenv("ADMIN_EMAILS", "")
    if not admin_emails:
        return
    db = next(get_db())
    try:
        for email in [e.strip() for e in admin_emails.split(",") if e.strip()]:
            crud.create_admin_if_not_exists(db, email)
    finally:
        db.close()


@app.post("/auth/login", response_model=schemas.LoginResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    admin = crud.get_admin_by_email(db, payload.email)
    if not admin:
        raise HTTPException(status_code=403, detail="This email is not registered as an admin.")
    token = auth.create_access_token(admin.email)
    return schemas.LoginResponse(access_token=token, admin_email=admin.email)


@app.post("/chat", response_model=schemas.ChatResponse)
def chat(
    payload: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(auth.get_current_admin),
):
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    result = intent_handler.process_message(db, payload.message)
    return schemas.ChatResponse(**result)


@app.get("/users", response_model=list[schemas.UserOut])
def get_users(db: Session = Depends(get_db), current_admin=Depends(auth.get_current_admin)):
    return crud.list_users(db)


@app.get("/health")
def health():
    return {"status": "ok"}