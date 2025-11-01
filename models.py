from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum

Base = declarative_base()

class TransactionType(enum.Enum):
    """Enum for transaction types"""
    INCOME = "income"
    EXPENSE = "expense"

class Transaction(Base):
    """Transaction model for storing budget data"""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert transaction to dictionary"""
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d'),
            'category': self.category,
            'amount': self.amount,
            'type': self.type.value,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, date={self.date}, category={self.category}, amount={self.amount})>"


class BudgetGoal(Base):
    """Budget goal model for category spending limits"""
    __tablename__ = 'budget_goals'
    
    id = Column(Integer, primary_key=True)
    category = Column(String(100), unique=True, nullable=False)
    monthly_limit = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert budget goal to dictionary"""
        return {
            'id': self.id,
            'category': self.category,
            'monthly_limit': self.monthly_limit,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f"<BudgetGoal(category={self.category}, limit={self.monthly_limit})>"