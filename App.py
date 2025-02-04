import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
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

st.title('BESS Revenue Forecast App')
st.write('Welcome to the BESS Revenue Forecast Analysis Tool')
st.write('Please navigate to the pages in the sidebar to submit or view forecasts.')
