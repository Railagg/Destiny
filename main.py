from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import json

from app.database import engine, get_db, Base
from app import models

# Создаем таблицы в базе данных (если их нет)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Destiny Game API")

# Разрешаем запросы от Telegram WebApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ВРЕМЕННО: пропускаем проверку Telegram для теста
def verify_telegram_data(init_data: dict) -> bool:
    return True

@app.get("/")
def root():
    return {
        "message": "Destiny API is working!",
        "status": "ok",
        "database": "connected",
        "version": "2.0"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/auth/telegram")
def auth_telegram(data: dict, db: Session = Depends(get_db)):
    # ... остальной код API ...
    return {"status": "ok"}
