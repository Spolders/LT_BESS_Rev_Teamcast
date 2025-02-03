import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import sqlite3
from datetime import datetime
import io

class BESSForecastDatabase:
    def __init__(self, db_path='forecasts.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS forecasts (
                id INTEGER PRIMARY KEY,
                start_year INTEGER,
                forecast_data TEXT,
                timestamp DATETIME
            )
        ''')
        self.conn.commit()

    def add_forecast(self, start_year, forecast):
        cursor = self.conn.cursor()
        forecast_str = ','.join(map(str, forecast))
        cursor.execute('INSERT INTO forecasts (start_year, forecast_data, timestamp) VALUES (?, ?, ?)', 
                       (start_year, forecast_str, datetime.now()))
        self.conn.commit()

    def get_all_forecasts(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT start_year, forecast_data FROM forecasts')
        return [(row[0], list(map(float, row[1].split(',')))) for row in cursor.fetchall()]

def parse_clipboard_data(clipboard_text):
    # Try to parse tab-separated or comma-separated data
    try:
        # First try reading as tab-separated
        df = pd.read_csv(io.StringIO(clipboard_text), sep='\t', header=None)
    except:
        try:
            # Then try comma-separated
            df = pd.read_csv(io.StringIO(clipboard_text), sep=',', header=None)
        except:
            return None, None
    
    # If single column, assume it's just values
    if df.shape[1] == 1:
        revenues = df[0].tolist()
        return None, revenues
    
    return None, df[1].tolist()

def calculate_forecast_distribution(all_forecasts):
    calendar_years_revenues = {}
    for start_year, forecast in all_forecasts:
        for i, revenue in enumerate(forecast):
            year = start_year + i
            if year not in calendar_years_revenues:
                calendar_years_revenues[year] = []
            calendar_years_revenues[year].append(revenue)
    
    distribution = {}
    for year, revenues in calendar_years_revenues.items():
        distribution[year] = {
            'mean': np.mean(revenues),
            'median': np.median(revenues),
            'std': np.std(revenues),
            '25th': np.percentile(revenues, 25),
            '75th': np.percentile(revenues, 75),
            'all_values': revenues
        }
    
    return distribution

def plot_forecast_distribution(distribution):
    years = list(distribution.keys())
    
    fig = go.Figure()
    
    if len(next(iter(distribution.values()))['all_values']) <= 6:
        for year in years:
            data = distribution[year]
            fig.add_trace(go.Scatter(
                x=[year]*len(data['all_values']),
                y=data['all_values'],
                mode='markers',
                name=f'{year} Forecasts',
                marker=dict(size=10, opacity=0.7)
