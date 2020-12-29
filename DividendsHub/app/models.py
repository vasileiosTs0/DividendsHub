from datetime import datetime
from app.extensions import db, login, mail
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    #First_name = db.Column(db.String(40), unique=True, nullable=False)    
    #Last_name = db.Column(db.String(120), unique=True, nullable=False)
    stocks = db.relationship('Stocks', backref='owner', lazy=True)
    deposits = db.relationship('Deposits', backref='owner', lazy=True)
    dividends = db.relationship('Dividends', backref='owner', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Stocks(db.Model):
    id = db.Column(db.Integer, primary_key=True)    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(60), nullable=False)
    amount_of_shares = db.Column(db.Float, nullable=False)
    cost_basis = db.Column(db.Float, nullable=False)
    sector = db.Column(db.String(60), nullable=False)

#    div_info = db.relationship('Dividend_info', backref='div_info', lazy=True)


    def __repr__(self):
        return f"Stock('{self.symbol}', '{self.name}', '{self.sector}', '{self.amount_of_shares}', '{self.cost_basis}')"

class Deposits(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    year = db.Column(db.Integer, nullable=False)  
    amount = db.Column(db.Float, nullable=False)    

    def __repr__(self):
        return f"Deposits('{self.amount}', '{self.date}', '{self.year}')"


class Dividends(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    year = db.Column(db.Integer, nullable=False)  
    amount = db.Column(db.Float, nullable=False)    
    symbol = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f"Dividends('{self.symbol}', '{self.amount}', '{self.date}', '{self.year}')"

#class Dividend_info(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    symbol = db.Column(db.Integer, db.ForeignKey('Stocks.symbol'), nullable=False, unique=True)
#    exDay = db.Column(db.Date, nullable=False, default=datetime.utcnow)
#    payDay = db.Column(db.Date, nullable=False)  
#    amount = db.Column(db.Float, nullable=False)    
#
#    div_info = db.relationship('Dividend_paid', backref='div_paid', lazy=True)
#
#    def __repr__(self):
#        return f"Dividend_info('{self.symbol}', '{self.exDay}', '{self.payDay}', '{self.amount}')"

#class Dividend_paid(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#    symbol = db.Column(db.String, db.ForeignKey('Dividend_info.symbol'), nullable=False)
#    payDay = db.Column(db.Date, nullable=False)  
#    amount = db.Column(db.Float, nullable=False)    
#
#    def __repr__(self):
#        return f"DivideDividend_paidnd_info('{self.user_id}', '{self.symbol}', '{self.payDay}', '{self.amount}')"

#class Portfolio(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#    portfolio_name = db.Column(db.String(60), nullable=False)

#    def __repr__(self):
#        return f"Portfolio('{self.user_id}', '{self.portfolio_name}')"
