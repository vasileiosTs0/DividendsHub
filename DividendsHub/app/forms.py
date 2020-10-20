from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField, DecimalField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from flask_wtf.file import FileField, FileAllowed
from app.models import User
from flask_login import current_user


class RegistrationForm(FlaskForm):
    username = StringField('Username:',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email:',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password:', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password:',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email:',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password:', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username:',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email:',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Update')
    delete = SubmitField('Delete Account')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')


class InsertStock(FlaskForm):
    ticker = StringField('Ticker:',
                           validators=[DataRequired(), Length(min=2, max=5)])
    number_of_shares = DecimalField('Number of shares:',
                        validators=[DataRequired()])
    cost_basis = DecimalField('Cost basis:',
                        validators=[DataRequired()])
    submit = SubmitField('Log stock')


class UploadPortfolio(FlaskForm):
    portfolio = FileField('Upload your portfolio:', validators=[FileAllowed(['xls', 'xlsx', 'csv'])])
    submit = SubmitField('Upload portfolio')


class EditStock(FlaskForm):
    number_of_shares = DecimalField('Number of shares:', default=0.0, validators=[NumberRange(min=0.00)])
    submit = SubmitField('Update stock')
    delete = SubmitField('Delete Stock')

class AddDeposit(FlaskForm):
    amount = DecimalField('Amount:',
                        validators=[DataRequired()])
    submit = SubmitField('Log Deposit')

class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password:', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password:',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class LogDividend(FlaskForm):
    amount = DecimalField('Amount:',
                        validators=[DataRequired()])
    ticker = StringField('Ticker:',
                           validators=[DataRequired(), Length(min=2, max=5)])
    submit = SubmitField('Log Dividend')
