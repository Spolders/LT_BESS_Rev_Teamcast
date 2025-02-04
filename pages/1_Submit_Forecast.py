# pages/1_Submit_Forecast.py
import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
import re

class BESSForecastDatabase:
    def __init__(self, db_path='forecasts.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS forecasts (
                id INTEGER PRIMARY KEY,
                start_year INTEGER,
                forecast_data TEXT,
                timestamp DATETIME,
                system_size FLOAT,
                location TEXT,
                battery_chemistry TEXT,
                use_case TEXT,
                premium BOOLEAN DEFAULT FALSE
            )
        ''')
        self.conn.commit()

    def add_forecast(self, start_year, forecast, metadata):
        cursor = self.conn.cursor()
        forecast_str = ','.join(map(str, forecast))
        cursor.execute('''
            INSERT INTO forecasts 
            (start_year, forecast_data, timestamp, system_size, location, 
             battery_chemistry, use_case, premium) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (start_year, forecast_str, datetime.now(), 
              metadata['system_size'], metadata['location'],
              metadata['battery_chemistry'], metadata['use_case'],
              metadata['premium']))
        self.conn.commit()

    def get_forecasts(self, premium=False, filters=None):
        cursor = self.conn.cursor()
        query = 'SELECT * FROM forecasts'
        if filters:
            conditions = []
            params = []
            for key, value in filters.items():
                if value:
                    conditions.append(f"{key} = ?")
                    params.append(value)
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
        
        cursor.execute(query, params if filters else None)
        return cursor.fetchall()

def parse_pasted_data(pasted_text):
    try:
        df = pd.read_csv(pd.io.common.StringIO(pasted_text), sep='\t', engine='python', header=None)
        if df.shape[0] < 2:
            return None, "Invalid format: Ensure you paste years and revenues"
        
        years = df.iloc[0].dropna().astype(int).tolist()
        revenues = df.iloc[1].dropna().apply(lambda x: float(re.sub(r'[^0-9.-]', '', str(x)))).tolist()
        
        if len(years) != len(revenues):
            return None, "Mismatched years and revenues"
        
        return (years[0], revenues), None
    except Exception as e:
        return None, f"Error parsing data: {e}"

def main():
    st.title('Submit BESS Revenue Forecast')
    
    # Premium user check (placeholder - implement actual authentication)
    is_premium = st.sidebar.checkbox('Premium User', value=False)
    
    db = BESSForecastDatabase()
    
    # Metadata collection
    st.subheader('Project Details')
    col1, col2 = st.columns(2)
    with col1:
        system_size = st.number_input('System Size (MWh)', min_value=0.0)
        location = st.selectbox('Location', ['North Germany', 'South Germany'])
    with col2:
        battery_chemistry = st.selectbox('Battery Chemistry', ['LFP', 'NMC', 'Other'])
        use_case = st.selectbox('Use Case', ['FCR', 'aFRR', 'Wholesale Trading'])

    # Forecast input
    st.subheader('Revenue Forecast')
    st.write('Paste years (first row) and revenues (second row)')
    pasted_data = st.text_area("Paste Excel data (tab-separated)")
    
    if st.button('Submit') and pasted_data:
        parsed_result, error = parse_pasted_data(pasted_data)
        if error:
            st.error(error)
        else:
            start_year, forecast_values = parsed_result
            metadata = {
                'system_size': system_size,
                'location': location,
                'battery_chemistry': battery_chemistry,
                'use_case': use_case,
                'premium': is_premium
            }
            db.add_forecast(start_year, forecast_values[:10], metadata)
            st.success('Forecast uploaded successfully!')

if __name__ == '__main__':
    main()
