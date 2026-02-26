from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем URL базы данных из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")

# Если DATABASE_URL не задан, используем SQLite для разработки
if not DATABASE_URL:
    logger.warning("⚠️ DATABASE_URL не задан, использую SQLite для разработки")
    DATABASE_URL = "sqlite:///./destiny.db"

# Для Render нужно заменить postgres:// на postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("✅ URL базы данных сконвертирован для PostgreSQL")

# Параметры подключения
engine_kwargs = {
    "pool_size": 5,
    "max_overflow": 10,
    "echo": False
}

# Для SQLite добавляем специальные параметры
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

# Создаем движок
engine = create_engine(DATABASE_URL, **engine_kwargs)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

def get_db():
    """Получить сессию базы данных (для FastAPI зависимостей)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_sync():
    """Получить сессию базы данных (для синхронного кода)"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def init_db():
    """Создать все таблицы в базе данных"""
    from models import Base as ModelsBase
    try:
        ModelsBase.metadata.create_all(bind=engine)
        logger.info("✅ Таблицы базы данных созданы/проверены")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблиц: {e}")
        return False

def check_connection():
    """Проверить подключение к базе данных"""
    try:
        with engine.connect() as conn:
            if DATABASE_URL.startswith("sqlite"):
                conn.execute("SELECT 1")
            else:
                conn.execute("SELECT 1")
        logger.info("✅ Подключение к базе данных успешно")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        return False

def get_db_info():
    """Получить информацию о базе данных"""
    from sqlalchemy import inspect
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        info = {
            "url": str(DATABASE_URL).split('@')[-1] if '@' in DATABASE_URL else 'SQLite',
            "tables": tables,
            "table_count": len(tables)
        }
        return info
    except Exception as e:
        logger.error(f"❌ Ошибка получения информации о БД: {e}")
        return {"error": str(e)}

# Проверяем подключение при импорте
if __name__ != "__main__":
    if check_connection():
        logger.info("✅ База данных готова к работе")
    else:
        logger.error("❌ База данных НЕДОСТУПНА!")
        init_db()

# При прямом запуске показываем информацию
if __name__ == "__main__":
    print("🔧 Тестирование базы данных...")
    if check_connection():
        print("✅ Подключение работает")
        print(f"📊 Информация о БД: {get_db_info()}")
    else:
        print("❌ Подключение не работает")
        if init_db():
            print("✅ База данных инициализирована")
