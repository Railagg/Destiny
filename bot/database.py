import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Получаем строку подключения из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ОШИБКА: DATABASE_URL не задана!")
    print("Добавь переменную окружения на Render")
    exit(1)

# Создаем подключение к базе данных
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Импортируем модели, чтобы они были известны Base
# Этот импорт должен быть ПОСЛЕ объявления Base, но ДО создания таблиц
from models import User, Character

# ПРИНУДИТЕЛЬНОЕ ПЕРЕСОЗДАНИЕ ТАБЛИЦ
print("=" * 40)
print("🔄 ПРОВЕРКА БАЗЫ ДАННЫХ")
print("=" * 40)
print("🗑️ Удаляем старые таблицы...")
Base.metadata.drop_all(bind=engine)
print("✅ Старые таблицы удалены")

print("🆕 Создаём новые таблицы...")
Base.metadata.create_all(bind=engine)
print("✅ Новые таблицы созданы успешно")
print("=" * 40)

def get_db():
    """Функция для получения сессии базы данных"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
