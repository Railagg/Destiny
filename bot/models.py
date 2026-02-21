from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import json

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    character = relationship("Character", back_populates="user", uselist=False)

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Основные параметры
    name = Column(String, default="Искатель")
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    
    # Ресурсы
    energy = Column(Integer, default=100)
    max_energy = Column(Integer, default=100)
    magic = Column(Integer, default=100)
    max_magic = Column(Integer, default=100)
    health = Column(Integer, default=100)
    max_health = Column(Integer, default=100)
    gold = Column(Integer, default=20)
    destiny_tokens = Column(Integer, default=0)
    
    # Характеристики
    strength = Column(Integer, default=1)
    dexterity = Column(Integer, default=1)
    intelligence = Column(Integer, default=1)
    vitality = Column(Integer, default=1)
    stat_points = Column(Integer, default=0)
    
    # Боевые параметры
    base_damage = Column(Integer, default=1)
    defense_bonus = Column(Integer, default=0)
    crit_chance = Column(Integer, default=0)
    crit_multiplier = Column(Integer, default=2)
    dodge_chance = Column(Integer, default=0)
    
    # Инвентарь (храним как JSON)
    inventory = Column(Text, default="[]")
    spells = Column(Text, default="[]")
    
    # Локация
    location = Column(String, default="start")
    
    # Класс персонажа
    player_class = Column(String, nullable=True)
    class_level = Column(Integer, default=1)
    class_exp = Column(Integer, default=0)
    
    # Дом
    house_level = Column(Integer, default=0)
    
    # Достижения
    achievements = Column(Text, default="[]")
    achievement_stats = Column(Text, default="{}")
    
    # Квесты
    completed_quests = Column(Text, default="[]")
    accepted_quests = Column(Text, default="[]")
    
    # Ежедневные
    daily_streak = Column(Integer, default=0)
    last_daily_claim = Column(Integer, default=0)
    
    # Кулдауны
    spell_cooldowns = Column(Text, default="{}")
    last_rest_time = Column(Integer, default=0)
    teleport_cooldown = Column(Integer, default=0)
    
    # Прочность инструментов
    pickaxe_durability = Column(Text, default="{}")
    fishing_rod_durability = Column(Text, default="{}")
    sickle_durability = Column(Text, default="{}")
    hoe_durability = Column(Text, default="{}")
    
    # Временные боевые эффекты
    blind_active = Column(Boolean, default=False)
    combat_state = Column(Text, nullable=True)
    
    # Временные метки обновления
    last_update = Column(Integer, default=0)
    last_magic_update = Column(Integer, default=0)
    last_daily_reset = Column(Integer, default=0)
    last_weekly_reset = Column(Integer, default=0)
    
    user = relationship("User", back_populates="character")
    
    def get_inventory(self):
        return json.loads(self.inventory) if self.inventory else []
    
    def set_inventory(self, inv_list):
        self.inventory = json.dumps(inv_list)
    
    def get_spells(self):
        return json.loads(self.spells) if self.spells else []
    
    def set_spells(self, spells_list):
        self.spells = json.dumps(spells_list)
    
    def get_achievements(self):
        return json.loads(self.achievements) if self.achievements else []
    
    def set_achievements(self, ach_list):
        self.achievements = json.dumps(ach_list)
    
    def get_achievement_stats(self):
        return json.loads(self.achievement_stats) if self.achievement_stats else {}
    
    def set_achievement_stats(self, stats_dict):
        self.achievement_stats = json.dumps(stats_dict)
    
    def get_completed_quests(self):
        return json.loads(self.completed_quests) if self.completed_quests else []
    
    def set_completed_quests(self, quests_list):
        self.completed_quests = json.dumps(quests_list)
    
    def get_accepted_quests(self):
        return json.loads(self.accepted_quests) if self.accepted_quests else []
    
    def set_accepted_quests(self, quests_list):
        self.accepted_quests = json.dumps(quests_list)
    
    def get_spell_cooldowns(self):
        return json.loads(self.spell_cooldowns) if self.spell_cooldowns else {}
    
    def set_spell_cooldowns(self, cooldowns_dict):
        self.spell_cooldowns = json.dumps(cooldowns_dict)
    
    def get_pickaxe_durability(self):
        return json.loads(self.pickaxe_durability) if self.pickaxe_durability else {}
    
    def set_pickaxe_durability(self, dur_dict):
        self.pickaxe_durability = json.dumps(dur_dict)
    
    def get_fishing_rod_durability(self):
        return json.loads(self.fishing_rod_durability) if self.fishing_rod_durability else {}
    
    def set_fishing_rod_durability(self, dur_dict):
        self.fishing_rod_durability = json.dumps(dur_dict)
    
    def get_sickle_durability(self):
        return json.loads(self.sickle_durability) if self.sickle_durability else {}
    
    def set_sickle_durability(self, dur_dict):
        self.sickle_durability = json.dumps(dur_dict)
    
    def get_hoe_durability(self):
        return json.loads(self.hoe_durability) if self.hoe_durability else {}
    
    def set_hoe_durability(self, dur_dict):
        self.hoe_durability = json.dumps(dur_dict)
    
    def get_combat_state(self):
        return json.loads(self.combat_state) if self.combat_state else None
    
    def set_combat_state(self, state_dict):
        self.combat_state = json.dumps(state_dict) if state_dict else None
