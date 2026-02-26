from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, JSON, Boolean, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import json
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String)
    last_name = Column(String)
    auth_date = Column(DateTime, default=datetime.utcnow)
    ton_wallet = Column(String, nullable=True)
    
    # ===== СИСТЕМА СТРИКА =====
    login_streak = Column(Integer, default=0)
    last_login = Column(Integer, default=0)
    max_streak = Column(Integer, default=0)
    premium_from_streak = Column(DateTime, nullable=True)
    streak_premium_days = Column(Integer, default=0)
    streak_history = Column(JSON, default=list)
    # ===========================
    
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
    
    # Гильдия
    guild_id = Column(Integer, nullable=True)
    guild_rank = Column(String, default="member")
    guild_join_time = Column(Integer, default=0)
    guild_leave_time = Column(Integer, default=0)
    guild_contribution = Column(Integer, default=0)
    guild_donated_gold = Column(Integer, default=0)
    guild_donated_dstn = Column(Integer, default=0)
    guild_wars = Column(Integer, default=0)
    
    character = relationship("Character", back_populates="user", uselist=False)
    
    def __repr__(self):
        return f"<User {self.telegram_id}>"

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Основные характеристики
    name = Column(String)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    
    # Здоровье и энергия
    health = Column(Integer, default=100)
    max_health = Column(Integer, default=100)
    health_regen = Column(Integer, default=0)
    energy = Column(Integer, default=100)
    max_energy = Column(Integer, default=100)
    last_update = Column(Integer, default=0)
    
    # Мана
    mana = Column(Integer, default=50)
    max_mana = Column(Integer, default=50)
    mana_regen = Column(Integer, default=0)
    last_mana_update = Column(Integer, default=0)
    
    # Атрибуты
    strength = Column(Integer, default=10)
    agility = Column(Integer, default=10)
    intelligence = Column(Integer, default=10)
    vitality = Column(Integer, default=10)
    luck = Column(Integer, default=0)
    
    # Ресурсы
    gold = Column(Integer, default=20)
    destiny_tokens = Column(Integer, default=0)
    stars = Column(Integer, default=0)
    ton = Column(Float, default=0)
    
    # Радужные ресурсы
    rainbow_shards = Column(Integer, default=0)
    rainbow_stones = Column(Integer, default=0)
    rainbow_craft_end = Column(Integer, default=0)
    rainbow_shards_collected = Column(Integer, default=0)
    rainbow_stones_used = Column(Integer, default=0)
    rainbow_history = Column(JSON, default=list)
    
    # Инвентарь
    _inventory = Column(Text, default="[]")
    
    # Экипировка
    equipped_weapon = Column(String, nullable=True)
    equipped_armor = Column(String, nullable=True)
    equipped_accessory = Column(String, nullable=True)
    
    # Локация
    location = Column(String, default="start")
    current_location = Column(String, default="start")
    
    # Класс
    player_class = Column(String, nullable=True)
    class_level = Column(Integer, default=1)
    
    # Боевые характеристики
    base_damage = Column(Integer, default=5)
    base_magic_damage = Column(Integer, default=2)
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
    
    # Класс-специфичные статы
    paladin_shield = Column(Integer, default=0)
    stealth = Column(Boolean, default=False)
    stealth_bonus = Column(Integer, default=0)
    rage = Column(Integer, default=0)
    totem_power = Column(Integer, default=0)
    spirit_power = Column(Integer, default=0)
    heal_power = Column(Integer, default=0)
    life_steal = Column(Integer, default=0)
    curse_power = Column(Integer, default=0)
    summon_power = Column(Integer, default=0)
    nature_power = Column(Integer, default=0)
    elemental_power = Column(Integer, default=0)
    
    # Боевые параметры
    current_health = Column(Integer, default=100)
    current_mana = Column(Integer, default=50)
    in_combat = Column(Boolean, default=False)
    combat_enemy = Column(String, nullable=True)
    combat_turn = Column(Integer, default=0)
    
    # Домик
    house_level = Column(Integer, default=0)
    house_furniture = Column(JSON, default=list)
    house_pets = Column(JSON, default=list)
    house_garden = Column(JSON, default=dict)
    house_buildings = Column(JSON, default=dict)
    last_rest_time = Column(Integer, default=0)
    
    # Питомцы
    pets = Column(JSON, default=list)
    active_pet = Column(Integer, nullable=True)
    pet_house_level = Column(Integer, default=1)
    
    # Квесты
    active_quests = Column(JSON, default=list)
    completed_quests = Column(JSON, default=list)
    completed_quests_count = Column(Integer, default=0)
    quest_progress = Column(JSON, default=dict)
    quest_points = Column(Integer, default=0)
    
    # Ежедневные квесты
    daily_quests = Column(JSON, default=dict)
    daily_quests_date = Column(String, nullable=True)
    
    # Ивенты
    event_tokens = Column(Integer, default=0)
    
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
    
    # NFT коллекция
    nft_collection = Column(JSON, default=list)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
        return self.inventory
    
    def add_item(self, item_id):
        inv = self.inventory
        inv.append(item_id)
        self.inventory = inv
    
    def remove_item(self, item_id):
        inv = self.inventory
        if item_id in inv:
            inv.remove(item_id)
            self.inventory = inv
            return True
        return False
    
    def has_item(self, item_id):
        return item_id in self.inventory
    
    def count_item(self, item_id):
        return self.inventory.count(item_id)
    
    def __repr__(self):
        return f"<Character {self.id} level {self.level}>"
