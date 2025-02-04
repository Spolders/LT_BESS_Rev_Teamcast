import streamlit as st
import pandas as pd
import numpy as np
from database import BESSForecastDatabase

def parse_pasted_data(pasted_text):
    try:
        df = pd.read_csv(pd.io.common.StringIO(pasted_text), sep='\t', header=None)
        
        if df.shape[0] != 2:
            return None, "Input must have exactly two rows: years and revenues"
            
        years = df.iloc[0].dropna().astype(int).tolist()
        revenues = df.iloc[1].dropna().apply(lambda x: float(str(x).replace('€', '').replace(',', ''))).tolist()
        
        if len(years) != len(revenues):
            return None, "Mismatched number of years and revenues"
        
        start_year = years[0]
        return (start_year, revenues), None
        
    except Exception as e:
        return None, f"Error parsing data: {str(e)}"

def main():
    st.title('Submit BESS Revenue Forecast')
    db = BESSForecastDatabase()
    
    st.subheader('Project Details')
    col1, col2 = st.columns(2)
    with col1:
        system_size = st.number_input('System Size (MWh)', min_value=0.0)
        location = st.selectbox('Location', ['North Germany', 'South Germany'])
    with col2:
        battery_chemistry = st.selectbox('Battery Chemistry', ['LFP', 'NMC', 'Other'])
        use_case = st.selectbox('Use Case', ['FCR', 'aFRR', 'Wholesale Trading'])

    st.subheader('Revenue Forecast')
    st.write('Paste two rows from Excel/Sheets: years in first row, revenues in second row')
    pasted_data = st.text_area("Paste your forecast data (tab-separated)")
    
    if st.button('Submit Forecast') and pasted_data:
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
                'premium': False
            }
            db.add_forecast(start_year, forecast_values, metadata)
            st.success('Forecast uploaded successfully!')

if __name__ == '__main__':
    main()