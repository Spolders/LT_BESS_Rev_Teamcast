import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import sqlite3
from datetime import datetime
import re

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
                bess_power_rating REAL,
                bess_energy_capacity REAL,
                max_cycles_per_day INTEGER,
                forecaster_type TEXT,
                forecaster_company TEXT,
                is_anonymous INTEGER,
                timestamp DATETIME
            )
        ''')
        self.conn.commit()

    def add_forecast(self, start_year, forecast, bess_power, bess_capacity, max_cycles, forecaster_type, forecaster_company, is_anonymous):
        cursor = self.conn.cursor()
        forecast_str = ','.join(map(str, forecast))
        cursor.execute('''
            INSERT INTO forecasts 
            (start_year, forecast_data, bess_power_rating, bess_energy_capacity, max_cycles_per_day, forecaster_type, forecaster_company, is_anonymous, timestamp) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', 
        (start_year, forecast_str, bess_power, bess_capacity, max_cycles, forecaster_type, forecaster_company, is_anonymous, datetime.now()))
        self.conn.commit()

    def get_all_forecasts(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT start_year, forecast_data FROM forecasts')
        return [(row[0], list(map(float, row[1].split(',')))) for row in cursor.fetchall()]

def parse_pasted_data(pasted_text):
    """Parses pasted text input and returns a list of (start_year, forecast_values)."""
    try:
        df = pd.read_csv(pd.io.common.StringIO(pasted_text), sep='\t', engine='python', header=None)
        if df.shape[0] < 2:
            return None, "Invalid format: Ensure you paste at least two rows (Years, Revenues)"
        
        years = df.iloc[0].dropna().astype(int).tolist()
        revenues = df.iloc[1].dropna().apply(lambda x: float(re.sub(r'[^0-9.-]', '', str(x)))).tolist()
        
        if len(years) != len(revenues):
            return None, "Mismatched number of years and revenues."
        
        start_year = years[0]
        return (start_year, revenues), None
    except Exception as e:
        return None, f"Error parsing data: {e}"

def main():
    st.title('BESS Revenue Forecast Ensemble')
    db = BESSForecastDatabase()

    st.header('Paste Your BESS Revenue Forecast (Years in First Row, Revenues in Second Row)')
    pasted_data = st.text_area("Paste your data from Excel with tab separation")

    st.subheader("Battery Specifications")
    bess_power = st.number_input("BESS Power Rating (MW)", min_value=0.0, value=1.0)
    bess_capacity = st.number_input("BESS Energy Capacity (MWh)", min_value=0.0, value=2.0)
    max_cycles = st.number_input("Maximum Cycles per Day", min_value=0.0, value=2.0, step=0.1)

    st.subheader("Forecaster Characteristics")
    forecaster_type = st.selectbox("Forecaster Type", ["Consultant", "Market data provider", "BESS optimizer", "BESS asset owner", "BESS debt financier", "Other"])
    forecaster_company = st.text_input("Forecaster Company Name")
    is_anonymous = st.checkbox("Anonymous Forecast")

    if st.button('Submit Forecast') and pasted_data:
        parsed_result, error = parse_pasted_data(pasted_data)
        if error:
            st.error(error)
        else:
            start_year, forecast_values = parsed_result
            if len(forecast_values) >= 10:
                db.add_forecast(start_year, forecast_values[:10], bess_power, bess_capacity, max_cycles, forecaster_type, forecaster_company, int(is_anonymous))
                st.success('Forecast uploaded successfully!')
            else:
                st.error('Please provide at least 10 years of revenue data.')

if __name__ == '__main__':
    main()
