from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ОШИБКА: DATABASE_URL не задана!")
    exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ПРИНУДИТЕЛЬНОЕ ПЕРЕСОЗДАНИЕ ТАБЛИЦ
print("🔄 Пересоздаем таблицы...")
Base.metadata.drop_all(bind=engine)  # Удаляем старые таблицы
Base.metadata.create_all(bind=engine)  # Создаём новые
print("✅ Таблицы пересозданы")

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
