import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import sqlite3
from datetime import datetime

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

def parse_pasted_data(pasted_text):
    """Parses pasted text input and returns a list of (start_year, forecast_values)."""
    try:
        df = pd.read_csv(pd.io.common.StringIO(pasted_text), sep='\t|,', engine='python')
        if df.shape[1] < 2:
            return None, "Invalid format: Ensure you paste at least two columns (Year, Revenue)"
        
        df.columns = ['Year', 'Revenue']  # Rename columns to expected names
        df = df.dropna()  # Remove empty rows
        df['Year'] = df['Year'].astype(int)
        df['Revenue'] = df['Revenue'].astype(float)
        
        start_year = df['Year'].min()
        forecast_values = df['Revenue'].tolist()
        
        return (start_year, forecast_values), None
    except Exception as e:
        return None, f"Error parsing data: {e}"

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
    
    for year in years:
        data = distribution[year]
        fig.add_trace(go.Box(
            x=[year] * len(data['all_values']),
            y=data['all_values'],
            name=str(year),
            boxmean=True
        ))
    
    fig.update_layout(
        title='BESS Revenue Forecast Distribution',
        xaxis_title='Year',
        yaxis_title='Revenue (€)',
        showlegend=False
    )
    
    return fig

def main():
    st.title('BESS Revenue Forecast Ensemble')
    db = BESSForecastDatabase()

    # Forecast Input
    st.header('Paste Your BESS Revenue Forecast (Year, Revenue)')
    pasted_data = st.text_area("Paste your data from Excel (Year, Revenue) with a comma or tab separator")
    
    if st.button('Submit Forecast') and pasted_data:
        parsed_result, error = parse_pasted_data(pasted_data)
        if error:
            st.error(error)
        else:
            start_year, forecast_values = parsed_result
            if len(forecast_values) >= 10:
                db.add_forecast(start_year, forecast_values[:10])
                st.success('Forecast uploaded successfully!')
            else:
                st.error('Please provide at least 10 years of revenue data.')
    
    # Ensemble Visualization
    st.header('Anonymous Forecast Distribution')
    all_forecasts = db.get_all_forecasts()
    
    if all_forecasts:
        distribution = calculate_forecast_distribution(all_forecasts)
        fig = plot_forecast_distribution(distribution)
        st.plotly_chart(fig)

        # Summary statistics
        st.subheader('Forecast Summary')
        summary_df = pd.DataFrame.from_dict({
            year: {
                'Mean Revenue': data['mean'],
                'Median Revenue': data['median'],
                'Std Deviation': data['std'],
                '25th Percentile': data['25th'],
                '75th Percentile': data['75th']
            } for year, data in distribution.items()
        }, orient='index')
        st.dataframe(summary_df)

        st.metric('Total Forecasts', len(all_forecasts))

if __name__ == '__main__':
    main()
