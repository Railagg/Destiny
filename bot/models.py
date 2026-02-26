from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с персонажем
    character = relationship("Character", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # Премиум статус
    premium_until = Column(DateTime, nullable=True)
    premium_plan = Column(String, nullable=True)
    premium_total_days = Column(Integer, default=0)
    premium_first_purchase = Column(Boolean, default=False)
    
    # Награды за верность
    renewal_3months = Column(Boolean, default=False)
    renewal_6months = Column(Boolean, default=False)
    renewal_1year = Column(Boolean, default=False)
    renewal_2years = Column(Boolean, default=False)
    renewal_3years = Column(Boolean, default=False)
    
    # Профиль
    profile_frame = Column(String, nullable=True)
    profile_aura = Column(String, nullable=True)
    titles = Column(JSON, default=list)
    
    # Достижения
    event_achievements = Column(JSON, default=list)
    event_stats = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<User(id={self.telegram_id}, username={self.username})>"

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    user = relationship("User", back_populates="character")
    
    # Основные характеристики
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    
    # Здоровье
    max_health = Column(Integer, default=100)
    health = Column(Integer, default=100)
    health_regen = Column(Integer, default=0)
    
    # Энергия
    max_energy = Column(Integer, default=100)
    energy = Column(Integer, default=100)
    last_update = Column(Integer, default=0)  # для восстановления энергии
    
    # Мана
    max_magic = Column(Integer, default=100)
    magic = Column(Integer, default=100)
    magic_regen = Column(Integer, default=0)
    last_magic_update = Column(Integer, default=0)  # для восстановления маны
    
    # Ресурсы
    gold = Column(Integer, default=0)
    dstn = Column(Integer, default=0)  # премиум-валюта
    
    # Радужные ресурсы
    rainbow_shards = Column(Integer, default=0)  # 🌈 осколки
    rainbow_stones = Column(Integer, default=0)  # 💎 камни
    rainbow_craft_end = Column(Integer, default=0)  # время окончания крафта камня
    rainbow_shards_collected = Column(Integer, default=0)  # всего собрано осколков
    rainbow_stones_used = Column(Integer, default=0)  # всего использовано камней
    rainbow_history = Column(JSON, default=list)  # история операций
    
    # Статы
    strength = Column(Integer, default=1)
    dexterity = Column(Integer, default=1)
    intelligence = Column(Integer, default=1)
    vitality = Column(Integer, default=1)
    luck = Column(Integer, default=0)
    
    # Боевые статы
    base_damage = Column(Integer, default=1)
    base_magic_damage = Column(Integer, default=1)
    defense_bonus = Column(Integer, default=0)
    magic_damage_bonus = Column(Integer, default=0)
    
    # Крит
    crit_chance = Column(Integer, default=0)
    crit_multiplier = Column(Float, default=2.0)
    magic_crit_chance = Column(Integer, default=0)
    
    # Защита
    dodge_chance = Column(Integer, default=0)
    block_chance = Column(Integer, default=0)
    block_amount = Column(Integer, default=0)
    magic_resist = Column(Integer, default=0)
    
    # Стихийные сопротивления
    fire_resist = Column(Integer, default=0)
    cold_resist = Column(Integer, default=0)
    poison_resist = Column(Integer, default=0)
    holy_resist = Column(Integer, default=0)
    shadow_resist = Column(Integer, default=0)
    
    # Стихийный урон
    fire_damage = Column(Integer, default=0)
    cold_damage = Column(Integer, default=0)
    poison_damage = Column(Integer, default=0)
    holy_damage = Column(Integer, default=0)
    shadow_damage = Column(Integer, default=0)
    
    # Класс
    player_class = Column(String, nullable=True)
    class_level = Column(Integer, default=1)
    
    # Класс-специфичные статы
    paladin_shield = Column(Integer, default=0)  # щит паладина
    stealth = Column(Boolean, default=False)  # скрытность разбойника
    stealth_bonus = Column(Integer, default=0)  # бонус к скрытности
    rage = Column(Integer, default=0)  # ярость воина
    totem_power = Column(Integer, default=0)  # сила тотемов шамана
    spirit_power = Column(Integer, default=0)  # сила духов шамана
    heal_power = Column(Integer, default=0)  # сила лечения друида
    life_steal = Column(Integer, default=0)  # вампиризм чернокнижника
    curse_power = Column(Integer, default=0)  # сила проклятий
    summon_power = Column(Integer, default=0)  # сила призыва
    nature_power = Column(Integer, default=0)  # сила природы друида
    elemental_power = Column(Integer, default=0)  # сила стихий
    
    # Локация
    current_location = Column(String, default="start")
    
    # Дом
    house_level = Column(Integer, default=0)
    house_furniture = Column(JSON, default=list)  # мебель в доме
    house_pets = Column(JSON, default=list)  # питомцы в доме
    house_garden = Column(JSON, default=dict)  # огород
    house_buildings = Column(JSON, default=dict)  # постройки
    last_rest_time = Column(Integer, default=0)  # время последнего отдыха
    
    # Инвентарь
    inventory = Column(JSON, default=list)
    equipped_weapon = Column(String, nullable=True)
    equipped_armor = Column(String, nullable=True)
    equipped_accessory = Column(String, nullable=True)
    
    # Квесты
    active_quests = Column(JSON, default=list)
    completed_quests = Column(JSON, default=list)
    completed_quests_count = Column(Integer, default=0)
    quest_progress = Column(JSON, default=dict)
    quest_points = Column(Integer, default=0)
    
    # Ежедневные квесты
    daily_quests = Column(JSON, default=dict)
    daily_quests_date = Column(String, nullable=True)  # дата последнего обновления
    
    # Ивенты
    event_tokens = Column(Integer, default=0)  # токены ивентов
    
    # Питомцы
    pets = Column(JSON, default=list)  # список питомцев
    active_pet = Column(Integer, nullable=True)  # ID активного питомца
    pet_house_level = Column(Integer, default=1)  # уровень домика для питомцев
    
    # Крафт
    crafting_level = Column(Integer, default=1)
    crafting_exp = Column(Integer, default=0)
    
    # Премиум бонусы
    gold_multiplier = Column(Float, default=1.0)
    exp_multiplier = Column(Float, default=1.0)
    luck_bonus = Column(Integer, default=0)
    chests_per_day = Column(Integer, default=0)
    inventory_slots_bonus = Column(Integer, default=0)
    house_rest_multiplier = Column(Float, default=1.0)
    pet_exp_gain = Column(Float, default=1.0)
    pet_happiness_bonus = Column(Integer, default=0)
    shop_discount = Column(Integer, default=0)
    extra_slot_auction = Column(Integer, default=0)
    rainbow_shard_weekly = Column(Integer, default=0)
    exchange_bonus = Column(JSON, default=dict)
    
    # Статистика
    login_streak = Column(Integer, default=0)
    last_login = Column(Integer, default=0)
    kills_total = Column(Integer, default=0)
    deaths_total = Column(Integer, default=0)
    pvp_wins = Column(Integer, default=0)
    pvp_losses = Column(Integer, default=0)
    items_crafted = Column(Integer, default=0)
    resources_gathered = Column(Integer, default=0)
    
    def get_inventory(self):
        """Получить инвентарь"""
        if isinstance(self.inventory, str):
            try:
                return json.loads(self.inventory)
            except:
                return []
        return self.inventory or []
    
    def set_inventory(self, inventory_list):
        """Установить инвентарь"""
        self.inventory = inventory_list
    
    def add_item(self, item_id, count=1):
        """Добавить предмет в инвентарь"""
        inventory = self.get_inventory()
        for _ in range(count):
            inventory.append(item_id)
        self.set_inventory(inventory)
    
    def remove_item(self, item_id, count=1):
        """Удалить предмет из инвентаря"""
        inventory = self.get_inventory()
        removed = 0
        new_inventory = []
        for item in inventory:
            if item == item_id and removed < count:
                removed += 1
            else:
                new_inventory.append(item)
        self.set_inventory(new_inventory)
        return removed
    
    def has_item(self, item_id, count=1):
        """Проверить наличие предмета"""
        inventory = self.get_inventory()
        return inventory.count(item_id) >= count
    
    def count_item(self, item_id):
        """Посчитать количество предмета"""
        inventory = self.get_inventory()
        return inventory.count(item_id)
    
    def __repr__(self):
        return f"<Character(user_id={self.user_id}, level={self.level})>"
