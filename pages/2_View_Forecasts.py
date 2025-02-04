import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from database import BESSForecastDatabase

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
    
    is_premium = st.sidebar.checkbox('Premium Access', value=False)
    
    db = BESSForecastDatabase()
    
    if is_premium:
        st.sidebar.markdown('---')
        st.sidebar.markdown('✨ Premium Features Coming Soon')
    
    forecasts = db.get_forecasts()
    
    if forecasts:
        distribution = calculate_forecast_distribution(forecasts)
        fig = plot_forecast_distribution(distribution)
        st.plotly_chart(fig)
        
        st.subheader('Forecast Summary')
        summary_df = pd.DataFrame.from_dict({
            year: {
                'Mean Revenue': data['mean'],
                'Median Revenue': data['median'],
                'Std Deviation': data['std']
            } for year, data in distribution.items()
        }, orient='index')
        st.dataframe(summary_df)

        st.metric('Total Forecasts', len(forecasts))
    else:
        st.info('No forecasts available yet.')

if __name__ == '__main__':
    main()
