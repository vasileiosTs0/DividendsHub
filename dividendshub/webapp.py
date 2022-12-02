# from datetime import datetime
import datetime
import os

import pandas as pd
from flask import Blueprint, render_template, flash, redirect, request, url_for, abort
from flask_security import current_user, login_required, login_user, logout_user
from flask_mail import Message
from pandas_finance import Equity
# from app import create_db as db
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.urls import url_parse

from dividendshub.extensions import db, mail
from dividendshub.forms import (LoginForm, RegistrationForm, UpdateAccountForm,
                                InsertStock, UploadPortfolio, EditStock,
                                AddDeposit, RequestResetForm, ResetPasswordForm,
                                LogDividend, AnalyseStock)
from dividendshub.helpers import (apology, login_required, lookup, company_info, company_stats, create_deposits_plot,
                                  create_sunburst_plots,
                                  create_dividend_plot, create_portfolio_indicator_plots,
                                  SMA_signal)
from dividendshub.models import User, Stocks, Deposits, Dividends

server_bp = Blueprint('main', __name__)


@server_bp.route('/')
def index():
    """Show portfolio of stocks"""
    total_cost_basis = 0
    total_market_value = 0
    total_income = 0
    stocks = []
    if current_user.is_authenticated:
        users_stocks = Stocks.query.filter_by(owner=current_user).order_by(Stocks.symbol.asc()).all()
        if users_stocks:
            for index, row in enumerate(users_stocks):
                # print(row, row.symbol)
                stock_info = lookup(row.symbol)
                cost_basis = float(row.amount_of_shares) * float(row.cost_basis)
                price = float(stock_info['Price'] * row.amount_of_shares)
                stocks.append(list((str(row.symbol), str(row.name), round(float(row.amount_of_shares), 2),
                                    round(cost_basis, 2), round(price, 2), float(stock_info['PE Ratio']))))
                total_cost_basis += stocks[index][3]
                total_market_value += stocks[index][4]
                dividend_info = company_stats(row.symbol)  # New
                total_income += round(dividend_info['ttmDividend'] * row.amount_of_shares, 2)  # New
            portofolio_yield = round(total_income / total_market_value * 100, 2)

            plot = create_portfolio_indicator_plots(users_stocks, portofolio_yield)
            return render_template("index.html", title='Home Page', stocks=stocks,
                                   total_cost_basis=round(total_cost_basis, 2),
                                   total_market_value=round(total_market_value, 2), plot=plot)

    return render_template("index.html", title='Home Page', stocks=stocks,
                           total_cost_basis=round(total_cost_basis, 2),
                           total_market_value=round(total_market_value, 2))


@server_bp.route("/about")
def about():
    return render_template('about.html', title='About')


@server_bp.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        # Retrieve email from db
        user = User.query.filter_by(email=form.email.data.lower()).first()
        # Check that email exists and password is correct
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('main.index')
            return redirect(next_page)
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@server_bp.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


def send_register_notification():
    msg = Message('New Register Notification',
                  sender=os.environ.get('MAIL_USERNAME'),
                  recipients=[os.environ.get('EMAIL')])
    msg.body = f'''Someone new just registered on your website.'''
    mail.send(msg)


def send_delete_notification():
    msg = Message('Delete Notification',
                  sender=os.environ.get('MAIL_USERNAME'),
                  recipients=[os.environ.get('EMAIL')])
    msg.body = f'''A user deleted their account.'''
    mail.send(msg)


@server_bp.route('/register/', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Hash the password
        hashed_password = generate_password_hash(form.password.data)
        # Create user 
        new_user = User(username=form.username.data, email=form.email.data.lower(), password=hashed_password)
        # Add user to the database
        db.session.add(new_user)
        db.session.commit()
        send_register_notification()
        flash(f'Your account has been created. You are now able to log in', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)


@server_bp.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():

        if form.delete.data:
            users_stocks = Stocks.query.filter_by(owner=current_user).all()
            if users_stocks:
                for stock in users_stocks:
                    db.session.delete(stock)
                    db.session.commit()
            users_deposits = Deposits.query.filter_by(owner=current_user).all()
            if users_deposits:
                for deposit in users_deposits:
                    db.session.delete(deposit)
                    db.session.commit()
            db.session.delete(current_user)
            db.session.commit()
            send_delete_notification()
            flash('Your account has been deleted!', 'success')
            return redirect(url_for('main.register'))

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('main.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('account.html', title='Account', form=form)


def open_portfolio(portfolio):
    _, f_ext = os.path.splitext(portfolio.filename)
    if f_ext == ".xlsx" or f_ext == ".xls":
        data = pd.read_excel(portfolio, header=0)
    elif f_ext == ".csv":
        data = pd.read_csv(portfolio, header=0, skip_blank_lines=True, skipinitialspace=True, encoding='latin-1')
    else:
        data = []
    return data


@server_bp.route("/diversification")
@login_required
def diversification():
    """Show portfolio diversification"""
    if current_user.is_authenticated:
        users_stocks = Stocks.query.filter_by(owner=current_user).order_by(Stocks.symbol.asc()).all()
        if users_stocks:
            plot = create_sunburst_plots(users_stocks)
            return render_template("portfolio_diversification.html", title='Your diversification', plot=plot)

    return render_template("portfolio_diversification.html", title='Your diversification')


@server_bp.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    #    print(current_user)
    if current_user:
        form = InsertStock()
        form1 = UploadPortfolio()
        if form.validate_on_submit():
            # Create stock 
            ticker = form.ticker.data
            # Check if stock is unique, if not, update cost_basis and amount of shares
            symbol = Stocks.query.filter_by(symbol=ticker, owner=current_user).first()
            if symbol:
                new_amount_of_shares = round(float(symbol.amount_of_shares) + float(form.number_of_shares.data), 2)
                new_cost_basis = round((float(symbol.amount_of_shares) * float(symbol.cost_basis) + float(
                    form.number_of_shares.data) * float(form.cost_basis.data)) / (new_amount_of_shares), 2)
                symbol.amount_of_shares = new_amount_of_shares
                symbol.cost_basis = new_cost_basis
                db.session.commit()
                flash('Your stock has been updated!', 'success')
            else:
                # Add stock to the database
                if company_info(ticker)['Industry'] == "Investment Trusts/Mutual Funds":
                    sector = 'ETF'
                else:
                    sector = Equity(ticker).sector
                new_stock = Stocks(symbol=ticker, name=lookup(ticker)['Name'],
                                   amount_of_shares=form.number_of_shares.data, cost_basis=form.cost_basis.data,
                                   sector=sector, owner=current_user)
                db.session.add(new_stock)
                db.session.commit()
                flash('Your stock has been logged!', 'success')
            return redirect(url_for('main.buy'))

        if form1.validate_on_submit():
            if form1.portfolio.data:
                df = open_portfolio(form1.portfolio.data)
                stocks = Stocks.query.filter_by(owner=current_user).all()
                if stocks:
                    for stock in stocks:
                        # print(stock.id)
                        db.session.delete(stock)
                        db.session.commit()

                # Update stocks of the user
                for index, row in df.iterrows():
                    ticker = row['Ticker']
                    stock = Stocks.query.filter_by(symbol=ticker, owner=current_user).first()
                    if lookup(ticker) == None:
                        continue
                    elif stock == None:
                        new_stock = Stocks(symbol=ticker, name=lookup(ticker)['Name'],
                                           amount_of_shares=float(row['Quantity']),
                                           cost_basis=float(row['Cost Per Share']), sector=Equity(ticker).sector,
                                           owner=current_user)
                        db.session.add(new_stock)
                        db.session.commit()
                    else:
                        new_amount_of_shares = round(float(stock.amount_of_shares) + float(row['Quantity']), 2)
                        new_cost_basis = round((float(stock.amount_of_shares) * float(stock.cost_basis) + float(
                            row['Quantity']) * float(row['Cost Per Share'])) / (new_amount_of_shares), 2)
                        stock.amount_of_shares = new_amount_of_shares
                        stock.cost_basis = new_cost_basis
                        db.session.commit()
                flash('Your portfolio has been logged!', 'success')
                return redirect(url_for('main.index'))
            else:
                return redirect(url_for('main.buy'))
    else:
        abort(403)
    return render_template('buy.html', title='Update Portfolio', form=form, form1=form1)


@server_bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    """Edit shares of portfolio"""
    form = EditStock()
    stocks = {}
    if current_user:
        users_stocks = Stocks.query.filter_by(owner=current_user).order_by(Stocks.symbol.asc()).all()
        if users_stocks:
            for stock in users_stocks:
                stocks[stock.symbol] = float(stock.amount_of_shares)
        else:
            flash('You do not own any stocks yet!', 'danger')
            return redirect(url_for('main.buy'))

        if form.validate_on_submit():
            ticker = request.form.get("symbol")
            # Update stocks table
            symbol = Stocks.query.filter_by(symbol=ticker, owner=current_user).first()
            if form.submit.data:
                if symbol:
                    if float(form.number_of_shares.data) > float(symbol.amount_of_shares):
                        flash('You do not have that many stocks!', 'danger')
                        return redirect(url_for('main.edit'))
                    elif float(form.number_of_shares.data) == float(symbol.amount_of_shares):
                        db.session.delete(symbol)
                        db.session.commit()
                        flash('Your position has been deleted!', 'success')
                        return redirect(url_for('main.edit'))
                    else:
                        new_amount_of_shares = float(symbol.amount_of_shares) - float(form.number_of_shares.data)
                        symbol.amount_of_shares = new_amount_of_shares
                        db.session.commit()
                        flash('Your position has been updated!', 'success')
                        return redirect(url_for('main.edit'))
            if form.delete.data:
                db.session.delete(symbol)
                db.session.commit()
                flash('Your position has been deleted!', 'success')
                return redirect(url_for('main.edit'))
    else:
        abort(403)
    return render_template('edit.html', title='Edit/Delete Positions', form=form, stocks=stocks)


@server_bp.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    """Get stock quote."""
    form = AddDeposit()
    if form.validate_on_submit():
        date = request.form.get("date")
        amount = form.amount.data
        year, month, day = date.split('-')

        date = datetime.date(int(year), int(month), int(day))

        new_deposit = Deposits(amount=amount, date=date, year=year, owner=current_user)
        db.session.add(new_deposit)
        db.session.commit()
        flash('Your deposit has been recorded!', 'success')
        return redirect(url_for('main.deposit'))

    return render_template("deposit.html", title='Log Deposit', form=form)


@server_bp.route("/deposits", methods=["GET", "POST"])
@login_required
def deposits():
    """Show history of deposits"""

    if request.method == "POST":
        if request.form['delete_button']:
            selections = request.form.getlist('selection')
            if len(selections) == 0:
                return redirect(url_for('main.deposits'))
            else:
                for selection in selections:
                    deposit = Deposits.query.filter_by(id=int(selection), owner=current_user).first()
                    db.session.delete(deposit)
                    db.session.commit()
                flash('Deleted!', 'success')
                return redirect(url_for('main.deposits'))

    else:
        deposits = Deposits.query.filter_by(owner=current_user)
        check = 0
        for deposit in deposits:
            check += 1
        if check == 0:
            flash('You do not have any deposits yet!', 'danger')
            return redirect(url_for('main.deposit'))

        years = Deposits.query.filter_by(owner=current_user).distinct(Deposits.year).order_by(Deposits.year.asc())
        # for year in years:
        #    print(year)
        yr = []
        deposits_table = []
        total = 0
        if years:
            for year in years:
                # print(year, year.year)
                yr.append(list((year.id, year.date, year.year, year.amount)))
                total += year.amount
                deposits_table.append(list((year.id, year.date.strftime("%Y-%m-%d"), year.amount)))
            df = pd.DataFrame(yr)
            df.columns = ['id', 'date', 'year', 'amount']

            # print("End of years")
            # print(df.head())

            if df['year'].nunique() >= 5:
                deposit_years = df['year'].unique()[-5:]
            else:
                deposit_years = df['year'].unique()
            # Screen for unique years

            Deposits_list = {}
            for i, year in enumerate(deposit_years):
                rows = Deposits.query.filter_by(owner=current_user, year=int(year)).all()
                deposits = [[None for i in range(3)] for j in range(len(rows))]
                for index, row in enumerate(rows):
                    # print(row)
                    year = row.date.strftime('%y')
                    month = row.date.strftime('%m')
                    deposits[index][0] = year
                    deposits[index][1] = int(month)
                    deposits[index][2] = float(row.amount)
                deposits = pd.DataFrame(deposits, columns=['Year', 'Month', 'Amount'])
                Deposits_list["deposits_" + str(i)] = deposits.copy()

            # Padding months
            for i, year in enumerate(deposit_years):
                for month in range(1, 13):
                    temp = Deposits_list["deposits_" + str(i)]
                    temp = temp.append({'Month': month, 'Amount': 0, 'Year': year}, ignore_index=True)
                    Deposits_list["deposits_" + str(i)] = temp

            # Summing months and keeping the last 12
            for i, year in enumerate(deposit_years):
                for month in range(1, 13):
                    temp = Deposits_list["deposits_" + str(i)]
                    amount = sum(temp['Amount'][temp['Month'] == month])
                    temp = temp.append({'Month': month, 'Amount': amount, 'Year': year}, ignore_index=True)
                    Deposits_list["deposits_" + str(i)] = temp
                Deposits_list["deposits_" + str(i)] = Deposits_list["deposits_" + str(i)].tail(12)
                Deposits_list["deposits_" + str(i)] = Deposits_list["deposits_" + str(i)].drop(['Year'], axis=1)
            bar = create_deposits_plot(Deposits_list, deposit_years)
            return render_template("deposits.html", deposits=deposits_table, total=total, plot=bar)

    # return render_template("deposits.html", deposits=deposits_table, plot=bar)


@server_bp.route("/compare", methods=["GET", "POST"])
def compare():
    """Compare two stocks"""

    if request.method == "POST":
        # Check ticker is provided and it exists
        ticker1 = request.form.get("ticker0")
        if not ticker1:
            return apology("need to add the tickers")

        tickers = [None] * int(request.form.get("Ticker_number"))
        for index, t in enumerate(tickers):
            tickers[index] = lookup(request.form.get(str('ticker' + str(index))))

        if not tickers[0]['Symbol']:  # or not symbol2['symbol'] or not symbol3['symbol']:
            return apology("no such stock ticker")

        # Find info about tickers of each tickers
        compare_data = [[None for i in range(len(tickers[0]))] for j in range(len(tickers))]
        elements = [None for i in range(len(tickers[0]))]
        for i, company in enumerate(tickers):
            for index, element in enumerate(tickers[i]):
                # print(f"{i} -> {index},{element}: {tickers[i][element]}")
                compare_data[i][index] = tickers[i][element]
                elements[index] = element
        return render_template("compared.html", stocks=compare_data, elements=elements)
    else:
        # Redirect user to login form
        return render_template("compare.html")


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender=os.environ.get('MAIL_USERNAME'),
                  recipients=[user.email])
    msg.body = f'''Hello {user.username},\n
To reset your password, visit the following link:\n
{url_for('main.reset_token', token=token, _external=True)}\n
If you did not make this request then simply ignore this email.
'''
    mail.send(msg)


@server_bp.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email from yourdividendtracker@gmail.com has been sent with instructions to reset your password.',
              'info')
        return redirect(url_for('main.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@server_bp.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('main.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Hash the password
        hashed_password = generate_password_hash(form.password.data)
        # Update password 
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('main.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


@server_bp.route("/dividends")
@login_required
def dividends():
    """Show dividends of portfolio"""
    div = []
    total = 0
    if current_user.is_authenticated:
        # Take data from database
        users_stocks = Stocks.query.filter_by(owner=current_user).order_by(Stocks.symbol.asc()).all()
        if users_stocks:
            for index, row in enumerate(users_stocks):
                # print(row, row.symbol)
                dividend_info = company_stats(row.symbol)
                if not dividend_info:
                    print(f"No dividend info for {row.symbol}")
                    div.append(list((row.symbol, row.name, 'NULL', 'NULL', 0, 0)))
                else:
                    # Create variables for the template pages 
                    #    <th scope="col">Symbol</th>
                    #    <th scope="col">Name</th>
                    #    <th scope="col">Ex-div date</th>
                    #    <th scope="col">Payment date</th>
                    #    <th scope="col">Amount</th>
                    #    <th scope="col">Total</th>
                    div.append(list((row.symbol, row.name, dividend_info['exDividendDate'], 'Feature coming soon',
                                     round(dividend_info['ttmDividend'], 2),
                                     round(float(dividend_info['ttmDividend']) * row.amount_of_shares, 2))))
                    total += round(dividend_info['ttmDividend'] * row.amount_of_shares, 2)
            if total > 0:
                plot = create_dividend_plot(users_stocks)
                return render_template("dividends.html", dividends=div, total=round(total, 2), plot=plot)

    return render_template("dividends.html", dividends=div, total=round(total, 2))


@server_bp.route("/log_dividends", methods=["GET", "POST"])
@login_required
def log_dividends():
    """Get stock quote."""
    form = LogDividend()
    if form.validate_on_submit():
        date = request.form.get("date")
        amount = form.amount.data
        ticker = form.ticker.data
        year, month, day = date.split('-')

        date = datetime.date(int(year), int(month), int(day))

        new_dividend = Dividends(symbol=ticker, amount=amount, date=date, year=year, owner=current_user)
        db.session.add(new_dividend)
        db.session.commit()
        flash('Your dividend has been recorded!', 'success')
        return redirect(url_for('main.log_dividends'))

    return render_template("log_dividends.html", title='Log Dividends', form=form)


@server_bp.route("/technical_analysis", methods=["GET", "POST"])
@login_required
def technical_analysis():
    """Analyse a stock"""
    #    print(current_user)
    if current_user:
        form = AnalyseStock()
        if form.validate_on_submit():
            # Analyse stock ticker
            ticker = form.ticker.data
            first_sma = int(form.First_SMA.data)
            second_sma = int(form.Second_SMA.data)
            third_sma = int(form.Third_SMA.data)
            rsi_period = int(form.RSI_period.data)
            print(ticker)
            # Check ticker is provided and it exists
            if not ticker:
                return apology("need to add the ticker")
            if lookup(ticker) == None:
                return apology("no such stock ticker")

            signal = SMA_signal(ticker, first_sma, second_sma, third_sma, rsi_period)

            return render_template("analysed.html", stock=signal)

    else:
        abort(403)
    return render_template('technical_analysis.html', title='Technical Analysis', form=form)


# server=Flask(__name__)
def protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.config.requests_pathname_prefix):
            dashapp.server.view_functions[view_func] = login_required(dashapp.server.view_functions[view_func])

    return dashapp


"""

#def register_dashapps(app):
print("Inside!!!")
from app.dashapp1.layout import layout
from app.dashapp1.callbacks import register_callbacks

# Meta tags for viewport responsiveness
meta_viewport = {"name": "viewport", "content": "width=device-width, initial-scale=1, shrink-to-fit=no"}
external_stylesheets=["./assets/responsive-sidebar.css"]
dashapp1 = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True, url_base_pathname='/dashboard/')
#dashapp1 = dash.Dash(__name__,
#                        server=app,
#                        url_base_pathname='/dashboard/',
#                        #assets_folder=get_root_path(__name__) + '/assets/',
#                        assets_external_path='./dashboard/assets',
#                        external_stylesheets=external_stylesheets)#,
                    #    meta_tags=[meta_viewport])


#with server_bp.app_context():
#    dashapp1.title = 'Dashboard'
#    dashapp1.layout = layout
#    register_callbacks(dashapp1)
dashapp1.title = 'Dashboard'
dashapp1.layout = layout
#register_callbacks(dashapp1)

#app = DispatcherMiddleware(Flask(__name__), {
#                            '/dashboard1': dashapp1.server
#    })
#print(app)
_protect_dashviews(dashapp1)


    #return dashapp1
    #print(dashapp1.config.meta_tags)
    #print(dashapp1.config.external_stylesheets)

"""


# server_dash = Flask(__name__)

# dash_app1 = dash.Dash(__name__,server=Flask(__name__), requests_pathname_prefix='/dashboard/',routes_pathname_prefix = "/", )
# dash_app2 = dash.Dash(__name__,server=Flask(__name__), requests_pathname_prefix='/reports/',routes_pathname_prefix = "/")
# dash_app1.layout = html.Div([html.H1('Hi there, I am app1 for dashboards')])
# dash_app2.layout = html.Div([html.H1('Hi there, I am app2 for reports')])
# dash_app1 = protect_dashviews(dash_app1)
# dash_app2 = protect_dashviews(dash_app2)

@server_bp.route("/dash")
@login_required
def dash():
    print("Done!")
    # return redirect('/dashboard')
    return render_template("coming_soon.html")
    # return redirect(url_for('main.account'))


# app = DispatcherMiddleware(server_bp, {
#                            '/dash': dashapp1.server
#    })


# @server_bp.route("/dash")
# def render_dashboard():
#    return redirect('/dashboard')


# @server_bp.route('/report')
# def render_reports():
#    return redirect('/reports')


# server_bp.wsgi_app = DispatcherMiddleware(Flask(__name__), {
#    '/dashboard': dash_app1.server,
#    '/reports': dash_app2.server
# })

@server_bp.app_errorhandler(404)
def error_404(error):
    return render_template('errors/404.html'), 404


@server_bp.app_errorhandler(403)
def error_403(error):
    return render_template('errors/403.html'), 403


@server_bp.app_errorhandler(500)
def error_500(error):
    return render_template('errors/500.html'), 500
