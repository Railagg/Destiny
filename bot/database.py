import os
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# ============================================
# ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ
# ============================================

def get_database_url():
    """Получить и подготовить URL базы данных"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        logger.warning("⚠️ DATABASE_URL не задан, использую SQLite для разработки")
        # Для локальной разработки
        return "sqlite:///./destiny.db"
    
    # Для Render нужно заменить postgres:// на postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        logger.info("✅ URL базы данных сконвертирован для PostgreSQL")
    
    return DATABASE_URL

# Получаем URL
DATABASE_URL = get_database_url()
logger.info(f"📦 Подключение к БД: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'SQLite'}")

# ============================================
# СОЗДАНИЕ ДВИЖКА
# ============================================

# Параметры для разных типов БД
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

# ============================================
# СОЗДАНИЕ СЕССИЙ
# ============================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Базовый класс для моделей
Base = declarative_base()

# Для обратной совместимости
Session = scoped_session(SessionLocal)

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БД
# ============================================

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

# ============================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ============================================

def init_db():
    """Создать все таблицы в базе данных"""
    try:
        # Импортируем модели здесь, чтобы избежать циклических импортов
        from models import Base as ModelsBase
        
        # Создаем таблицы
        ModelsBase.metadata.create_all(bind=engine)
        
        # Проверяем, что таблицы создались
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info(f"✅ База данных инициализирована. Таблицы: {', '.join(tables)}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы данных: {e}")
        return False

def check_connection():
    """Проверить подключение к базе данных"""
    try:
        with engine.connect() as conn:
            if DATABASE_URL.startswith("sqlite"):
                conn.execute(text("SELECT 1"))
            else:
                conn.execute(text("SELECT 1"))
        logger.info("✅ Подключение к базе данных успешно")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        return False

def get_db_info():
    """Получить информацию о базе данных"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        info = {
            "url": str(DATABASE_URL).split('@')[-1] if '@' in DATABASE_URL else 'SQLite',
            "tables": tables,
            "table_count": len(tables)
        }
        
        # Для каждой таблицы получаем количество записей
        table_stats = {}
        with engine.connect() as conn:
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    table_stats[table] = count
                except:
                    table_stats[table] = "ошибка"
        
        info["table_stats"] = table_stats
        return info
    except Exception as e:
        logger.error(f"❌ Ошибка получения информации о БД: {e}")
        return {"error": str(e)}

def reset_db(confirm=False):
    """СБРОСИТЬ БАЗУ ДАННЫХ (только для разработки!)"""
    if not confirm:
        logger.warning("⚠️ Сброс БД требует подтверждения!")
        return False
    
    try:
        from models import Base as ModelsBase
        ModelsBase.metadata.drop_all(bind=engine)
        ModelsBase.metadata.create_all(bind=engine)
        logger.warning("⚠️ База данных сброшена и пересоздана!")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка сброса БД: {e}")
        return False

# ============================================
# МИГРАЦИИ (для будущих обновлений)
# ============================================

def run_migrations():
    """Запустить миграции базы данных"""
    try:
        from alembic.config import Config
        from alembic import command
        
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("✅ Миграции выполнены успешно")
        return True
    except ImportError:
        logger.info("📦 Alembic не установлен, пропускаем миграции")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка выполнения миграций: {e}")
        return False

# ============================================
# АВТОМАТИЧЕСКАЯ ИНИЦИАЛИЗАЦИЯ
# ============================================

# При импорте файла проверяем подключение
if __name__ != "__main__":
    # Проверяем подключение при импорте
    if check_connection():
        logger.info("✅ База данных готова к работе")
    else:
        logger.error("❌ База данных НЕДОСТУПНА!")
        
        # Пробуем инициализировать
        if init_db():
            logger.info("✅ База данных инициализирована")
        else:
            logger.error("❌ Не удалось инициализировать БД")

# ============================================
# ТЕСТИРОВАНИЕ (при прямом запуске)
# ============================================

if __name__ == "__main__":
    print("🔧 Тестирование базы данных...")
    
    # Проверяем подключение
    if check_connection():
        print("✅ Подключение работает")
    else:
        print("❌ Подключение не работает")
        exit(1)
    
    # Инициализируем БД
    if init_db():
        print("✅ Инициализация успешна")
    else:
        print("❌ Инициализация не удалась")
    
    # Информация о БД
    info = get_db_info()
    print(f"\n📊 Информация о БД:")
    print(f"  📁 Тип: {info['url']}")
    print(f"  📋 Таблицы: {info['tables']}")
    print(f"  📊 Статистика: {info.get('table_stats', {})}")
