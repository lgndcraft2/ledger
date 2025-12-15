from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_phone = db.Column(db.String(20), nullable=False)
    
    # CRITICAL FIX: Changed from String(10) to String(50)
    transaction_type = db.Column(db.String(50), nullable=False) 
    
    party_name = db.Column(db.String(100), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    
    # RECOMMENDED FIX: Changed Float to Numeric for money precision
    # If you prefer Float for simplicity, you can keep it as db.Float
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    amount_paid = db.Column(db.Numeric(10, 2), nullable=False)
    
    @property
    def balance(self):
        # Convert to float for easy math in Python if using Numeric
        return float(self.total_amount) - float(self.amount_paid)

    def __repr__(self):
        return f"<Txn {self.transaction_type}: {self.item_name}>"
    

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)