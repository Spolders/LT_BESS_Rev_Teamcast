def create_tables(self):
    cursor = self.conn.cursor()
    # Drop existing table to reset schema
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
