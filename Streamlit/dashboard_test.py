import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json

# Title
st.title("Electricity Spot Market Prices Dashboard")

# Sidebar for user input
st.sidebar.header("Select Date Range")
start_date = st.sidebar.date_input("Start Date", value=datetime(2021, 11, 1))
end_date = st.sidebar.date_input("End Date", value=datetime(2021, 11, 2))

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
    'end_date': f'{end_date}T00:00',
    'time_trunc': 'hour'
}

# Fetch Data from API
response = requests.get(endpoint + get_archives, headers=headers, params=params)

if response.status_code == 200:
    st.success("Data fetched successfully!")
    data_json = response.json()

    # Extract Spot Market Data
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

    # Plot using Plotly
    fig = px.line(data, x='Time', y='Price (€/MWh)', title='Spot Market Prices Over Time',
                  labels={'Price (€/MWh)': 'Price (€/MWh)', 'Time': 'Time'})
    fig.update_layout(xaxis_title="Time", yaxis_title="Price (€/MWh)", title_x=0.5)

    # Display plot
    st.plotly_chart(fig, use_container_width=True)

    # Display raw data
    with st.expander("Show raw data"):
        st.dataframe(data)
else:
    st.error(f"Failed to fetch data. Status Code: {response.status_code}")


