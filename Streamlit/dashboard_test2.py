import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json

# Title
st.title("Electricity Spot Market Prices Dashboard")

# Sidebar for user input
st.sidebar.header("Date Range Selection")
st.sidebar.write("Default range is the past 3 months.")

# Calculate default date range (last 3 months)
default_start_date = (datetime.now() - timedelta(days=30)).date()
default_end_date = datetime.now().date()

# Sidebar date input
start_date = st.sidebar.date_input("Start Date", value=default_start_date, min_value=default_start_date)
end_date = st.sidebar.date_input("End Date", value=default_end_date, min_value=start_date)

if start_date > end_date:
    st.sidebar.error("Start Date cannot be after End Date. Please adjust your selection.")

# API Details
endpoint = 'https://apidatos.ree.es'
get_archives = '/en/datos/mercados/precios-mercados-tiempo-real'
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Host': 'apidatos.ree.es'
}

params = {
    'start_date': f'{start_date}T00:00',
    'end_date': f'{end_date}T23:59',
    'time_trunc': 'hour'
}

# Fetch Data from API
st.sidebar.header("Data Fetching")
with st.spinner("Fetching data..."):
    response = requests.get(endpoint + get_archives, headers=headers, params=params)

if response.status_code == 200:
    st.sidebar.success("Data fetched successfully!")
    data_json = response.json()

    # Extract Spot Market Data
    try:
        spot_market_data = data_json['included'][1]
        spot_values = spot_market_data['attributes']['values']

        # Process data
        prices = []
        times = []
        for data_point in spot_values:
            prices.append(data_point['value'])
            times.append(datetime.strptime(data_point['datetime'], "%Y-%m-%dT%H:%M:%S.%f%z"))

        # Create DataFrame
        data = pd.DataFrame({'Time': times, 'Price (€/MWh)': prices})

        # Display Plotly interactive chart
        fig = px.line(data, x='Time', y='Price (€/MWh)', title='Spot Market Prices Over Time',
                      labels={'Price (€/MWh)': 'Price (€/MWh)', 'Time': 'Time'})
        fig.update_layout(xaxis_title="Time", yaxis_title="Price (€/MWh)", title_x=0.5)

        # Display plot
        st.plotly_chart(fig, use_container_width=True)

        # Interactive DataTable
        with st.expander("Show raw data"):
            st.dataframe(data)

    except KeyError:
        st.error("Unexpected response structure. Please check the API data format.")
else:
    st.sidebar.error(f"Failed to fetch data. Status Code: {response.status_code}")
    st.error("Data could not be retrieved. Please check your internet connection or API settings.")
