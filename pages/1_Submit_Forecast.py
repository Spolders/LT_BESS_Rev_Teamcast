import streamlit as st
import pandas as pd
import re
from database import BESSForecastDatabase

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
    
    is_premium = st.sidebar.checkbox('Premium User', value=False)
    
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
