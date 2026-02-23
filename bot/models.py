from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import json
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с персонажем
    character = relationship("Character", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.telegram_id}>"

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Основные характеристики
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    
    # Здоровье и энергия
    health = Column(Integer, default=100)
    max_health = Column(Integer, default=100)
    energy = Column(Integer, default=100)
    max_energy = Column(Integer, default=100)
    magic = Column(Integer, default=50)
    max_magic = Column(Integer, default=50)
    
    # Ресурсы
    gold = Column(Integer, default=20)
    destiny_tokens = Column(Integer, default=0)
    
    # Инвентарь (храним как JSON строку)
    _inventory = Column(Text, default="[]")
    
    # Локация
    location = Column(String, default="start")
    
    # Класс
    player_class = Column(String, nullable=True)
    class_level = Column(Integer, default=1)
    
    # Характеристики класса
    strength = Column(Integer, default=1)
    dexterity = Column(Integer, default=1)
    intelligence = Column(Integer, default=1)
    vitality = Column(Integer, default=1)
    
    # Боевые характеристики
    luck = Column(Integer, default=0)
    crit_chance = Column(Integer, default=0)
    crit_multiplier = Column(Integer, default=2)
    dodge_chance = Column(Integer, default=0)
    defense_bonus = Column(Integer, default=0)
    base_damage = Column(Integer, default=5)
    
    # ========== НОВЫЕ БОЕВЫЕ ПАРАМЕТРЫ ==========
    current_health = Column(Integer, default=100)   # текущее здоровье в бою
    current_mana = Column(Integer, default=50)       # текущая мана в бою
    in_combat = Column(Boolean, default=False)       # в бою или нет
    combat_enemy = Column(String, nullable=True)     # id врага
    combat_turn = Column(Integer, default=0)         # 0 - атака, 2 - защита
    # ==============================================
    
    # Домик
    house_level = Column(Integer, default=0)
    house_furniture = Column(JSON, default=list)
    
    # Питомцы
    pets = Column(JSON, default=list)
    active_pet = Column(Integer, nullable=True)
    
    # Системные поля
    login_streak = Column(Integer, default=0)
    last_login = Column(Integer, default=0)  # timestamp
    last_update = Column(Integer, default=0)  # timestamp для энергии
    last_magic_update = Column(Integer, default=0)  # timestamp для магии
    
    # Связь с пользователем
    user = relationship("User", back_populates="character")
    
    @property
    def inventory(self):
        """Получить инвентарь как список"""
        try:
            return json.loads(self._inventory) if self._inventory else []
        except:
            return []
    
    @inventory.setter
    def inventory(self, value):
        """Сохранить инвентарь как JSON строку"""
        self._inventory = json.dumps(value, ensure_ascii=False)
    
    def get_inventory(self):
        """Вернуть инвентарь (для совместимости)"""
        return self.inventory
    
    def add_item(self, item_id):
        """Добавить предмет в инвентарь"""
        inv = self.inventory
        inv.append(item_id)
        self.inventory = inv
    
    def remove_item(self, item_id):
        """Удалить предмет из инвентаря"""
        inv = self.inventory
        if item_id in inv:
            inv.remove(item_id)
            self.inventory = inv
            return True
        return False
    
    def has_item(self, item_id):
        """Проверить наличие предмета"""
        return item_id in self.inventory
    
    def __repr__(self):
        return f"<Character {self.id} level {self.level}>"

# Создаем таблицы
def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы")
