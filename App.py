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
    
    # Create figure
    fig = go.Figure()
    
    # Add scatter for all points if few forecasts
    if len(next(iter(distribution.values()))['all_values']) <= 6:
        for year in years:
            data = distribution[year]
            fig.add_trace(go.Scatter(
                x=[year]*len(data['all_values']),
                y=data['all_values'],
                mode='markers',
                name=f'{year} Forecasts',
                marker=dict(size=10, opacity=0.7)
            ))
    else:
        # Box plot for distribution
        for year in years:
            data = distribution[year]
            fig.add_trace(go.Box(
                x=[year]*len(data['all_values']),
                y=data['all_values'],
                name=str(year),
                boxmean=True
            ))
    
    fig.update_layout(
        title='BESS Revenue Forecast Distribution',
        xaxis_title='Year',
        yaxis_title='Revenue (€)',
        showlegend=True
    )
    
    return fig

def main():
    st.title('BESS Revenue Forecast Ensemble')
    db = BESSForecastDatabase()

    # Forecast Input
    st.header('Upload Your BESS Revenue Forecast')
    start_year = st.number_input('Forecast Start Year', min_value=2024, max_value=2030, value=datetime.now().year)
    
    forecast_input = [
        st.number_input(f'Revenue for {start_year + i} (€)', value=0.0, key=f'year_{i}') 
        for i in range(10)
    ]
    
    if st.button('Submit Forecast'):
        if len(forecast_input) == 10 and all(x >= 0 for x in forecast_input):
            db.add_forecast(start_year, forecast_input)
            st.success('Forecast uploaded anonymously!')
        else:
            st.error('Invalid forecast. Ensure 10 years of non-negative values.')

    # Ensemble Visualization
    st.header('Anonymous Forecast Distribution')
    all_forecasts = db.get_all_forecasts()
    
    if all_forecasts:
        # Calculate distribution
        distribution = calculate_forecast_distribution(all_forecasts)
        
        # Plot distribution
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
