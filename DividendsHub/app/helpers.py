import os
import sqlite3
import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import pandas_datareader.data as web
import plotly.express as px
import flask
import requests
import urllib
import json 

from datetime import datetime as dt
from flask import Flask, flash, jsonify, redirect, render_template, request, session, current_app
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from dash import Dash
import dash_html_components as html
from pandas_finance import Equity
from functools import wraps

with open('/etc/config.json') as config_file:
    config = json.load(config_file)


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = config.get('IEX_CLOUD_key')
        response = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        if quote["peRatio"] == None:
            quote["peRatio"] = 0.0
        if quote["marketCap"] == None:
            quote["marketCap"] = 0.0
        if quote["week52High"] == None:
            quote["week52High"] = 0.0
        if quote["week52Low"] == None:
            quote["week52Low"] = 0.0
        if quote["ytdChange"] == None:
            quote["ytdChange"] = 0.0
        if quote["latestPrice"] == None:
            quote["latestPrice"] = 0.0
        return {
            "Name": quote["companyName"],
            "Price": float(quote["latestPrice"]),
            "Symbol": quote["symbol"],
            "PE Ratio": float(quote["peRatio"]),
            "Exchange": quote["primaryExchange"],
            "Market Cap": float(quote["marketCap"]),
            "52 Week High": float(quote["week52High"]),
            "52 Week Low": float(quote["week52Low"]),
            "YTD Change": float(quote["ytdChange"])
        }
    except (KeyError, TypeError, ValueError):
        return None

def company_info(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = config.get('IEX_CLOUD_key')
        response = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/company?token={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "Sector": quote["sector"],
            "Description": quote["description"],
            "Employees": quote["employees"],
            "Industry": quote["industry"]
        }
    except (KeyError, TypeError, ValueError, None):
        return None

def company_stats(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = config.get('IEX_CLOUD_key')
        response = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/stats?token={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        if quote["beta"] == None:
            quote["beta"] = 0.0
        if quote["marketcap"] == None:
            quote["marketcap"] = 0.0
        if quote["dividendYield"] == None:
            quote["dividendYield"] = 0.0
        if quote["ttmDividendRate"] == None:
            quote["ttmDividendRate"] = 0.0
        if quote["ttmEPS"] == None:
            quote["ttmEPS"] = 0.0
        if quote["day50MovingAvg"] == None:
            quote["day50MovingAvg"] = 0.0
        if quote["day200MovingAvg"] == None:
            quote["day200MovingAvg"] = 0.0
        if quote["year5ChangePercent"] == None:
            quote["year5ChangePercent"] = 0.0
        if quote["year2ChangePercent"] == None:
            quote["year2ChangePercent"] = 0.0
        if quote["year1ChangePercent"] == None:
            quote["year1ChangePercent"] = 0.0
        if quote["ytdChangePercent"] == None:
            quote["ytdChangePercent"] = 0.0
        if quote["month6ChangePercent"] == None:
            quote["month6ChangePercent"] = 0.0
        if quote["month3ChangePercent"] == None:
            quote["month3ChangePercent"] = 0.0
        if quote["month1ChangePercent"] == None:
            quote["month1ChangePercent"] = 0.0
        if quote["day30ChangePercent"] == None:
            quote["day30ChangePercent"] = 0.0
        if quote["day5ChangePercent"] == None:
            quote["day5ChangePercent"] = 0.0
        if quote["ytdChangePercent"] == None:
            quote["ytdChangePercent"] = 0.0
        if quote["exDividendDate"] == None:
            quote["exDividendDate"] = "None"
        if quote["nextEarningsDate"] == None:
            quote["nextEarningsDate"] = "None"
        return {
            "MarketCap": float(quote["marketcap"]),
            "Beta": float(quote["beta"]),
            "exDividendDate": quote["exDividendDate"],
            "nextEarningsDate": quote["nextEarningsDate"],
            "DividendYield": float(quote["dividendYield"]),
            "ttmDividend": float(quote["ttmDividendRate"]),
            "ttmEPS": float(quote["ttmEPS"]),
            "day50MovingAvg": float(quote["day50MovingAvg"]),
            "day200MovingAvg": float(quote["day200MovingAvg"]),
            "year5ChangePercent": float(quote["year5ChangePercent"]),
            "year2ChangePercent": float(quote["year2ChangePercent"]),
            "year1ChangePercent": float(quote["year1ChangePercent"]),
            "ytdChangePercent": float(quote["ytdChangePercent"]),
            "month6ChangePercent": float(quote["month6ChangePercent"]),
            "month3ChangePercent": float(quote["month3ChangePercent"]),
            "month1ChangePercent": float(quote["month1ChangePercent"]),
            "day30ChangePercent": float(quote["day30ChangePercent"]),
            "day5ChangePercent": float(quote["day5ChangePercent"])
        }
    except (KeyError, TypeError, ValueError):
        return None

def dividend(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = config.get('IEX_CLOUD_key')
        response = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/dividends/next?token={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        if quote["amount"] == None:
            quote["amount"] = 0.0
        elif quote["exDate"] == None:
            quote["exDate"] = "None"
        elif quote["paymentDate"] == None:
            quote["paymentDate"] = "None"
        return {
            "exDate": quote["exDate"],
            "price": float(quote["amount"]),
            "payDate": quote["paymentDate"],
            "frequency": quote["frequency"]
        }
    except (KeyError, TypeError, ValueError):
        return None

def company_info2(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = config.get('FINNHUB_key')
        response = requests.get(f"https://finnhub.io/api/v1/stock/profile2?symbol={urllib.parse.quote_plus(symbol)}&token={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "Industry": quote["finnhubIndustry"]
        }
    except (KeyError, TypeError, ValueError, None):
        return None

def company_peers(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = config.get('FINNHUB_key')
        response = requests.get(f"https://finnhub.io/api/v1/stock/peers?symbol={urllib.parse.quote_plus(symbol)}&token={api_key}")
        #response = requests.get(f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/peers?token={api_key}")
        response.raise_for_status()
        quote = response.json()

    except requests.RequestException:
        return None
    return quote



def find_sector(sector):
    pass

def create_deposits_plot(Deposits_list, years):
    labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    if len(years) >= 5:
        fig = go.Figure(data=[
            go.Bar(y=Deposits_list["deposits_0"]['Amount'], x=labels, name=str(years[0])),
            go.Bar(y=Deposits_list["deposits_1"]['Amount'], x=labels, name=str(years[1])),
            go.Bar(y=Deposits_list["deposits_2"]['Amount'], x=labels, name=str(years[2])),
            go.Bar(y=Deposits_list["deposits_3"]['Amount'], x=labels, name=str(years[3])),
            go.Bar(y=Deposits_list["deposits_4"]['Amount'], x=labels, name=str(years[4]))
        ])
    elif len(years) >= 4:
        fig = go.Figure(data=[
            go.Bar(y=Deposits_list["deposits_0"]['Amount'], x=labels, name=str(years[0])),
            go.Bar(y=Deposits_list["deposits_1"]['Amount'], x=labels, name=str(years[1])),
            go.Bar(y=Deposits_list["deposits_2"]['Amount'], x=labels, name=str(years[2])),
            go.Bar(y=Deposits_list["deposits_3"]['Amount'], x=labels, name=str(years[3]))
        ])
    elif len(years) >= 3:
        fig = go.Figure(data=[
            go.Bar(y=Deposits_list["deposits_0"]['Amount'], x=labels, name=str(years[0])),
            go.Bar(y=Deposits_list["deposits_1"]['Amount'], x=labels, name=str(years[1])),
            go.Bar(y=Deposits_list["deposits_2"]['Amount'], x=labels, name=str(years[2]))
        ])
    elif len(years) >= 2:
        fig = go.Figure(data=[
            go.Bar(y=Deposits_list["deposits_0"]['Amount'], x=labels, name=str(years[0])),
            go.Bar(y=Deposits_list["deposits_1"]['Amount'], x=labels, name=str(years[1]))
        ])
    else:   
        fig = go.Figure(data=[
                go.Bar(y=Deposits_list["deposits_0"]['Amount'], x=labels, name=str(years[0]))
        ])
    fig.update_layout(barmode='group')
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

def create_sunburst_plots(users_stocks):
    indx = [None for j in range(len(users_stocks))]
    name = [None for j in range(len(users_stocks))]
    sector = [None for j in range(len(users_stocks))]
    sect = [None for j in range(len(users_stocks))]
    value = [None for j in range(len(users_stocks))]
    weight = [None for j in range(len(users_stocks))]
    price = [None for j in range(len(users_stocks))]
    dividends = [None for j in range(len(users_stocks))]
    dividend_yield = [None for j in range(len(users_stocks))]
    dividend_date = [None for j in range(len(users_stocks))]
    #month = [None for j in range(len(users_stocks))]

    portfolio_yield = 0
    stocks = 0
    for index, row in enumerate(users_stocks):
        indx[index] = int(index)
        name[index] = row.symbol
        sector[index] = row.sector
        if sector[index] == "Consumer Defensive":
            sector[index] = "Consumer<br>Defensive"
        elif sector[index] == "Communication Services":
            sector[index] = "Communication<br>Services"
        elif sector[index] == "Consumer Cyclical":
            sector[index] = "Consumer<br>Cyclical"

        sect[index] = row.sector
        value[index] = round(float(row.cost_basis)*row.amount_of_shares,2)
        price[index] = round(lookup(row.symbol)["Price"]*row.amount_of_shares,2)
    
        dividend_info = company_stats(row.symbol)
        if not dividend_info:
            dividends[index] = 0
            dividend_yield[index] = 0
            dividend_date[index] = "None"
        else:
            dividends[index] = round(float(dividend_info['ttmDividend'])*row.amount_of_shares,2)
            dividend_yield[index] = round(dividend_info['DividendYield'] * 100,2)
            # Need to change 'exDividendDate' with the 'payDate'
            dividend_date[index] = (dividend_info['exDividendDate'])
            #month[index] = dt.strptime(dividend_info['exDividendDate'], '%Y-%m-%d').month
        portfolio_yield += dividend_yield[index]*row.amount_of_shares
        stocks += row.amount_of_shares 

    diversification = pd.DataFrame(list(zip(indx, sector, name, value)), columns =['', 'sector', 'name', 'value'])
    current_diversification = pd.DataFrame(list(zip(indx, sector, name, price)), columns =['', 'sector', 'name', 'value'])

    levels = ['name','sector']
    color_columns = ['value', diversification['value'].sum()]
    value_column = ['value']

    df_initial_diversification = build_hierarchical_dataframe(diversification, levels, value_column, color_columns)
    df_current_diversification = build_hierarchical_dataframe(current_diversification, levels, value_column, color_columns)

    fig = make_subplots(1, 2, specs=[[{"type": "domain"}, {"type": "domain"}]], subplot_titles =('Initial Allocation:','Current Allocation:'))
    fig.add_trace(go.Sunburst(
        labels=df_initial_diversification['id'],
        parents=df_initial_diversification['parent'],
        values=df_initial_diversification['value'],
        branchvalues='total',
        marker=dict(
            colors=df_initial_diversification['color'],
            colorscale='GnBu_r'),
        #    title=dict(
        #        text='Initial diversification'),
        hovertemplate='<b>%{label} </b> <br> Value: %{value}<br> Weight: %{color:.2f}%',
        name='',
        maxdepth=2
        ), 1, 1)

    fig.add_trace(go.Sunburst(
        labels=df_current_diversification['id'],
        parents=df_current_diversification['parent'],
        values=df_current_diversification['value'],
        branchvalues='total',
        marker=dict(
            colors=df_current_diversification['color'],
            colorscale='GnBu_r'),
        #title=dict(
        #    text='Current diversification'),
        hovertemplate='<b>%{label} </b> <br> Value: %{value}<br> Weight: %{color:.2f}%',
        name='',
        maxdepth=2
        ), 1, 2)


    fig.update_layout(height=300, plot_bgcolor='#ffffff',paper_bgcolor='#ffffff', margin=dict(l=10,r=10,b=0,t=50))

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON
    
def create_portfolio_indicator_plots(users_stocks, port_yield):
    indx = [None for j in range(len(users_stocks))]
    name = [None for j in range(len(users_stocks))]
    sect = [None for j in range(len(users_stocks))]
    value = [None for j in range(len(users_stocks))]
    price = [None for j in range(len(users_stocks))]
    dividends = [None for j in range(len(users_stocks))]
    dividend_yield = [None for j in range(len(users_stocks))]
    dividend_date = [None for j in range(len(users_stocks))]
    #month = [None for j in range(len(users_stocks))]

    portfolio_yield = 0
    stocks = 0
    for index, row in enumerate(users_stocks):
        indx[index] = int(index)
        name[index] = row.symbol
        sect[index] = row.sector
        value[index] = round(float(row.cost_basis)*row.amount_of_shares,2)
        price[index] = round(lookup(row.symbol)["Price"]*row.amount_of_shares,2)
    
        dividend_info = company_stats(row.symbol)
        if not dividend_info:
            dividends[index] = 0
            dividend_yield[index] = 0
            dividend_date[index] = "None"
        else:
            dividends[index] = round(float(dividend_info['ttmDividend'])*row.amount_of_shares,2)
            dividend_yield[index] = round(dividend_info['DividendYield'] * 100,2)
            # Need to change 'exDividendDate' with the 'payDate'
            dividend_date[index] = (dividend_info['exDividendDate'])
#           month[index] = dt.strptime(dividend_info['exDividendDate'], '%Y-%m-%d').month
        portfolio_yield += dividend_yield[index]*row.amount_of_shares
        stocks += row.amount_of_shares 
    portfolio_yield = portfolio_yield/stocks
    
    gauges_data = pd.DataFrame(list(zip(indx, sect, name, value, price)), columns =['', 'sector', 'name', 'value', 'price'])

    fig = make_subplots(1, 3, specs=[[{"type": "domain"}, {"type": "domain"}, {"type": "domain"}]],)
    #indic_port = go.Figure()
    if gauges_data['price'].sum() >= gauges_data['value'].sum():
        color = "green"
    else:
        color = "red"


    fig.add_trace(go.Indicator(
        mode = "number+gauge+delta",
        delta = {'reference': gauges_data['value'].sum()},
        value = gauges_data['price'].sum(),
        number = {'prefix': "$"},
        gauge = {
            'axis' : {'tickprefix': "$"},
            'bar' : {'color': color}
        },
        domain = {'x': [0.2, 0.8], 'y': [0.1, 0.5]},
        title = {'text': "Portfolio Value, $"}),1,1)

    if float(gauges_data['price'].sum()/gauges_data['value'].sum() * 100)-100 >= 0:
        color = "green"
    else:
        color = "red"

    fig.add_trace(go.Indicator(
        mode = "number+gauge",
        delta = {'reference': 0},
        value = (float(gauges_data['price'].sum()/gauges_data['value'].sum() * 100)-100),
        number = {'suffix': "%"},
        domain = {'x': [0.2, 0.8], 'y': [0.1, 0.5]},
        gauge = {
            'axis' : {'ticksuffix': "%"},
            'bar' : {'color': color}
        },
        title = {'text': "Portfolio Performance, %"}),1,2)
    
    fig.add_trace(go.Indicator(
        mode = "number+gauge",
        delta = {'reference': 0},
        value = (port_yield),
        number = {'suffix': "%"},
        domain = {'x': [0.2, 0.8], 'y': [0.1, 0.5]},
        gauge = {
            'axis' : {'ticksuffix': "%"},
            'bar' : {'color': color}
        },
        title = {'text': "Portfolio Yield, %"}),1,3)
    fig.update_layout(height=150, plot_bgcolor='#ffffff',paper_bgcolor='#ffffff', margin=dict(l=10,r=10,b=10,t=60,pad=4))

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def build_hierarchical_dataframe(df, levels, value_column, color_columns=None):
    """
    Build a hierarchy of levels for Sunburst or Treemap charts.

    Levels are given starting from the bottom to the top of the hierarchy,
    ie the last level corresponds to the root.
    """
    # Define a new dataframe
    df_all_trees = pd.DataFrame(columns=['id', 'parent', 'value', 'color'])
    # Loop through the level


    for i, level in enumerate(levels):
        
        df_tree = pd.DataFrame(columns=['id', 'parent', 'value', 'color'])
        dfg = df.groupby(levels[i:]).sum()
        dfg = dfg.reset_index()
        df_tree['id'] = dfg[level].copy()
        if i < len(levels) - 1:
            df_tree['parent'] = dfg[levels[i+1]].copy()
        else:
            df_tree['parent'] = 'total'
        #print(df_tree['parent'])
        df_tree['value'] = dfg[value_column]
        df_tree['color'] = dfg[color_columns[0]] / df['value'].sum() *100
        df_all_trees = df_all_trees.append(df_tree, ignore_index=True)

    total = pd.Series(dict(id='total', parent='',
                              value=df['value'].sum(),
                              color=df[color_columns[0]].sum() / df['value'].sum() *100))
    df_all_trees = df_all_trees.append(total, ignore_index=True)
    return df_all_trees


def create_dividend_plot(users_stocks):
    indx = [None for j in range(len(users_stocks))]
    name = [None for j in range(len(users_stocks))]
    sector = [None for j in range(len(users_stocks))]
    sect = [None for j in range(len(users_stocks))]
    value = [None for j in range(len(users_stocks))]
    weight = [None for j in range(len(users_stocks))]
    price = [None for j in range(len(users_stocks))]
    dividends = [None for j in range(len(users_stocks))]
    dividend_yield = [None for j in range(len(users_stocks))]
    dividend_date = [None for j in range(len(users_stocks))]
    month = [None for j in range(len(users_stocks))]

    #portfolio_yield = 0
    #stocks = 0
    counter = 0
    for index, row in enumerate(users_stocks):
        indx[counter] = int(counter)
        name[counter] = row.symbol
        sector[counter] = row.sector
        if sector[counter] == "Consumer Defensive":
            sector[counter] = "Consumer<br>Defensive"
        elif sector[counter] == "Communication Services":
            sector[counter] = "Communication<br>Services"

        sect[counter] = row.sector
        value[counter] = round(float(row.cost_basis)*row.amount_of_shares,2)
        price[counter] = round(lookup(row.symbol)["Price"]*row.amount_of_shares,2)
    
        dividend_info = company_stats(row.symbol)
        if dividend_info['DividendYield'] == 0.0:
            continue
	    #dividends[index] = 0
            #dividend_yield[index] = 0
            #dividend_date[index] = "None"
        else:
            dividends[counter] = round(float(dividend_info['ttmDividend'])*row.amount_of_shares,2)
            dividend_yield[counter] = round(dividend_info['DividendYield'] * 100,2)
            # Need to change 'exDividendDate' with the 'payDate'
            dividend_date[counter] = (dividend_info['exDividendDate'])
            month[counter] = dt.strptime(dividend_info['exDividendDate'], '%Y-%m-%d').month
            counter += 1
	#portfolio_yield += dividend_yield[index]*row.amount_of_shares
        #stocks += row.amount_of_shares 

    diversification = pd.DataFrame(list(zip(indx, sector, name, value)), columns =['', 'sector', 'name', 'value'])
    dividend_pay_data = pd.DataFrame(list(zip(indx, sect, name, dividends)), columns =['', 'sector', 'name', 'value'])

    levels = ['name','sector']
    color_columns = ['value', diversification['value'].sum()]
    value_column = ['value']

    df_dividend_diversification = build_hierarchical_dataframe(dividend_pay_data, levels, value_column, color_columns)

    total_divs = dividend_pay_data['value'].sum()
    average = total_divs/dividend_pay_data.size
    fig = go.Figure(go.Treemap(
        labels = df_dividend_diversification['id'],
        parents = df_dividend_diversification['parent'],
        values =  df_dividend_diversification['value'],
        branchvalues='total',
        marker=dict(
            colors=df_dividend_diversification['color'],
            colorscale='BuGn_r',
            cmid = average),
        textinfo = "label+value+percent parent+percent root",
        hovertemplate='<b>%{label} </b> <br> Value: %{value}<br> Weight: %{color:.2f}',
        name='',
        ))
    fig.update_layout(height=250, plot_bgcolor='#ffffff',paper_bgcolor='#ffffff', margin=dict(l=10,r=10,b=0,t=15,pad=4))

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON
