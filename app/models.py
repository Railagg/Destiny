from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
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
    
    character = relationship("Character", back_populates="user", uselist=False)

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    name = Column(String)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    health = Column(Integer, default=100)
    max_health = Column(Integer, default=100)
    mana = Column(Integer, default=50)
    max_mana = Column(Integer, default=50)
    strength = Column(Integer, default=10)
    agility = Column(Integer, default=10)
    intelligence = Column(Integer, default=10)
    gold = Column(Integer, default=0)
    destiny_tokens = Column(Integer, default=0)
    inventory = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="character")
