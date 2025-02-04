import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from database import BESSForecastDatabase

def get_filtered_forecasts(db, filters):
    cursor = db.conn.cursor()
    query = '''SELECT start_year, forecast_data, system_size, location, 
               battery_chemistry, use_case FROM forecasts WHERE 1=1'''
    params = []
    
    if filters['location']:
        query += ' AND location = ?'
        params.append(filters['location'])
    if filters['battery_chemistry']:
        query += ' AND battery_chemistry = ?'
        params.append(filters['battery_chemistry'])
    if filters['use_case']:
        query += ' AND use_case = ?'
        params.append(filters['use_case'])
    if filters['min_size'] is not None:
        query += ' AND system_size >= ?'
        params.append(filters['min_size'])
    if filters['max_size'] is not None:
        query += ' AND system_size <= ?'
        params.append(filters['max_size'])
    
    cursor.execute(query, params)
    return cursor.fetchall()

def calculate_distribution(forecasts):
    years_revenues = {}
    for row in forecasts:
        start_year = row[0]
        revenues = list(map(float, row[1].split(',')))
        for i, revenue in enumerate(revenues):
            year = start_year + i
            if year not in years_revenues:
                years_revenues[year] = []
            years_revenues[year].append(revenue)
    return years_revenues

def plot_distribution(years_revenues, filter_text):
    fig = go.Figure()
    for year in sorted(years_revenues.keys()):
        revenues = years_revenues[year]
        fig.add_trace(go.Box(
            x=[year] * len(revenues),
            y=revenues,
            name=str(year),
            boxpoints='outliers',
            boxmean=True
        ))
    
    title = 'BESS Revenue Forecast Distribution'
    if filter_text:
        title += f'\n{filter_text}'
    
    fig.update_layout(
        title=title,
        xaxis_title='Year',
        yaxis_title='Revenue (€)',
        showlegend=False,
        height=600
    )
    return fig

def main():
    st.title('BESS Revenue Teamcast - Premium View')
    
    db = BESSForecastDatabase()
    
    with st.sidebar:
        st.header('Filter Forecasts')
        location = st.selectbox('Location', ['', 'North Germany', 'South Germany'])
        battery_chemistry = st.selectbox('Battery Chemistry', ['', 'LFP', 'NMC', 'Other'])
        use_case = st.selectbox('Use Case', ['', 'FCR', 'aFRR', 'Wholesale Trading'])
        
        st.subheader('System Size (MWh)')
        size_range = st.slider('Range', 0.0, 1000.0, (0.0, 1000.0), 10.0)
        min_size, max_size = size_range
        
        filters = {
            'location': location,
            'battery_chemistry': battery_chemistry,
            'use_case': use_case,
            'min_size': min_size if min_size > 0 else None,
            'max_size': max_size if max_size < 1000 else None
        }
        
        filter_text = ' | '.join(f'{k}: {v}' for k, v in filters.items() 
                               if v and k not in ['min_size', 'max_size'])
        if min_size > 0 or max_size < 1000:
            filter_text += f' | Size: {min_size}-{max_size} MWh'

    forecasts = get_filtered_forecasts(db, filters)
    
    if forecasts:
        years_revenues = calculate_distribution(forecasts)
        
        st.plotly_chart(plot_distribution(years_revenues, filter_text))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric('Filtered Forecasts', len(forecasts))
        
        st.subheader('Filtered Statistics')
        stats = {}
        for year in sorted(years_revenues.keys()):
            revenues = years_revenues[year]
            stats[year] = {
                'Mean': np.mean(revenues),
                'Median': np.median(revenues),
                'Std Dev': np.std(revenues),
                'Min': np.min(revenues),
                'Max': np.max(revenues)
            }
        
        stats_df = pd.DataFrame(stats).T
        st.dataframe(stats_df.style.format({
            'Mean': '€{:,.0f}',
            'Median': '€{:,.0f}',
            'Std Dev': '€{:,.0f}',
            'Min': '€{:,.0f}',
            'Max': '€{:,.0f}'
        }))
        
        # Download functionality
        csv = pd.DataFrame(forecasts, columns=['Start Year', 'Revenues', 'System Size', 
                                             'Location', 'Chemistry', 'Use Case']).to_csv()
        st.download_button('Download Filtered Data', csv, 'filtered_forecasts.csv')
    else:
        st.info('No forecasts match the selected filters.')

if __name__ == '__main__':
    main()