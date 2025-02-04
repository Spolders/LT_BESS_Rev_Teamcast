import sqlite3
from datetime import datetime

class BESSForecastDatabase:
    def __init__(self, db_path='forecasts.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS forecasts')
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

    def get_forecasts(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT start_year, forecast_data FROM forecasts')
        return [(row[0], list(map(float, row[1].split(',')))) for row in cursor.fetchall()]
