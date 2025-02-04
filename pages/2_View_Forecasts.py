```python
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from database import BESSForecastDatabase

def calculate_distribution(all_forecasts):
    years_revenues = {}
    for start_year, forecast in all_forecasts:
        for i, revenue in enumerate(forecast):
            year = start_year + i
            if year not in years_revenues:
                years_revenues[year] = []
            years_revenues[year].append(revenue)
    return years_revenues

def plot_distribution(years_revenues):
    fig = go.Figure()
    for year in sorted(years_revenues.keys()):
        revenues = years_revenues[year]
        fig.add_trace(go.Box(
            x=[year] * len(revenues),
            y=revenues,
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
    st.title('BESS Revenue Forecasts')
    db = BESSForecastDatabase()
    cursor = db.conn.cursor()
    cursor.execute('SELECT start_year, forecast_data FROM forecasts')
    rows = cursor.fetchall()
    
    if rows:
        forecasts = [(row[0], list(map(float, row[1].split(',')))) for row in rows]
        years_revenues = calculate_distribution(forecasts)
        fig = plot_distribution(years_revenues)
        st.plotly_chart(fig)
    else:
        st.info('No forecasts available yet.')

if __name__ == '__main__':
    main()
```
