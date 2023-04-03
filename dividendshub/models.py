from datetime import datetime
from dividendshub.extensions import db, login, mail
from werkzeug.security import check_password_hash, generate_password_hash
from flask_security import UserMixin, RoleMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, unique=False, default=False)
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
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

# class Dividend_info(db.Model):
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

# class Dividend_paid(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#    symbol = db.Column(db.String, db.ForeignKey('Dividend_info.symbol'), nullable=False)
#    payDay = db.Column(db.Date, nullable=False)  
#    amount = db.Column(db.Float, nullable=False)    
#
#    def __repr__(self):
#        return f"DivideDividend_paidnd_info('{self.user_id}', '{self.symbol}', '{self.payDay}', '{self.amount}')"

# class Portfolio(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#    portfolio_name = db.Column(db.String(60), nullable=False)

#    def __repr__(self):
#        return f"Portfolio('{self.user_id}', '{self.portfolio_name}')"
