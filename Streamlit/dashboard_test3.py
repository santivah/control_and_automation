import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

# Title
st.title("Electricity Spot Market Prices Dashboard")

# Sidebar for user input
st.sidebar.header("Options")
show_detailed_analysis = st.sidebar.checkbox("Show Detailed Analysis")

# Calculate default date range (last 30 days)
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
with st.spinner("Fetching data..."):
    response = requests.get(endpoint + get_archives, headers=headers, params=params)

if response.status_code == 200:
    data_json = response.json()

    try:
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
        data['Date'] = data['Time'].dt.date
        data['Hour'] = data['Time'].dt.hour

        # Main Dashboard
        st.subheader("Electricity Prices Over the Selected Period")
        fig = px.line(data, x='Time', y='Price (€/MWh)', title='Spot Market Prices Over Time',
                      labels={'Price (€/MWh)': 'Price (€/MWh)', 'Time': 'Time'})
        fig.update_layout(xaxis_title="Time", yaxis_title="Price (€/MWh)", title_x=0.5)
        st.plotly_chart(fig, use_container_width=True)

        # Show raw data
        with st.expander("Show raw data"):
            st.dataframe(data)

        # Detailed Analysis
        if show_detailed_analysis:
            st.subheader("Detailed Analysis")

            # Lowest price analysis for the past week
            last_week = data[data['Date'] >= (datetime.now().date() - timedelta(days=7))]
            daily_min = last_week.groupby('Date').apply(lambda x: x.loc[x['Price (€/MWh)'].idxmin()])
            st.markdown("### Lowest Electricity Prices Per Day (Last 7 Days)")
            st.dataframe(daily_min[['Date', 'Hour', 'Price (€/MWh)']])

            # Expected trend for the next day
            st.markdown("### Expected Trend for the Next Day")
            next_day_prices = np.sin(np.linspace(0, 2 * np.pi, 24)) + 50  # Example of synthetic data
            next_day_hours = pd.date_range(datetime.now() + timedelta(days=1), periods=24, freq='H')
            next_day_df = pd.DataFrame({'Time': next_day_hours, 'Price (€/MWh)': next_day_prices})
            next_day_fig = px.line(next_day_df, x='Time', y='Price (€/MWh)', title="Expected Prices for Tomorrow")
            st.plotly_chart(next_day_fig, use_container_width=True)

            # Lowest price forecast for the next day
            min_idx = next_day_df['Price (€/MWh)'].idxmin()
            st.markdown(f"### Time of Lowest Price for Tomorrow")
            st.write(f"The lowest price is expected at {next_day_df['Time'][min_idx].strftime('%H:%M')} "
                     f"with a value of {next_day_df['Price (€/MWh)'][min_idx]:.2f} €/MWh.")
    except KeyError:
        st.error("Unexpected response structure. Please check the API data format.")
else:
    st.error(f"Failed to fetch data. Status Code: {response.status_code}")
