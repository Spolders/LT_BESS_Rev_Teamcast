# pages/2_View_Forecasts.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime
from Submit_Forecast import BESSForecastDatabase

def plot_forecast_distribution(distribution, filters=None):
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
    
    title = 'BESS Revenue Forecast Distribution'
    if filters:
        filter_text = ' | '.join(f'{k}: {v}' for k, v in filters.items() if v)
        title += f'\n{filter_text}'
    
    fig.update_layout(
        title=title,
        xaxis_title='Year',
        yaxis_title='Revenue (€)',
        showlegend=False
    )
    return fig

def main():
    st.title('BESS Revenue Forecast Ensemble')
    
    is_premium = st.sidebar.checkbox('Premium Access', value=False)
    
    db = BESSForecastDatabase()
    
    filters = {}
    if is_premium:
        st.sidebar.header('Filters')
        filters['location'] = st.sidebar.selectbox('Location', ['', 'North Germany', 'South Germany'])
        filters['battery_chemistry'] = st.sidebar.selectbox('Battery Chemistry', ['', 'LFP', 'NMC', 'Other'])
        filters['use_case'] = st.sidebar.selectbox('Use Case', ['', 'FCR', 'aFRR', 'Wholesale Trading'])
        
        # Additional premium features can be added here
        st.sidebar.markdown('---')
        st.sidebar.markdown('✨ Premium Features')
        st.sidebar.markdown('- Filtered view of forecasts')
        st.sidebar.markdown('- Detailed statistics')
        st.sidebar.markdown('- Export capabilities')
    
    forecasts = db.get_forecasts(premium=is_premium, filters=filters if is_premium else None)
    
    if forecasts:
        fig = plot_forecast_distribution(forecasts, filters if is_premium else None)
        st.plotly_chart(fig)
        
        if is_premium:
            st.download_button(
                'Download Data',
                data=pd.DataFrame(forecasts).to_csv(index=False),
                file_name='bess_forecasts.csv',
                mime='text/csv'
            )
    else:
        st.info('No forecasts available for the selected filters.')

if __name__ == '__main__':
    main()
