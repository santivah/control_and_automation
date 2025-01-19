import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, timezone
import numpy as np


# Title
# Set page configuration
st.set_page_config(
    page_title="REDUCING CO2 EMISSIONS WHILE CHARGING A LAPTOP",
    page_icon="⚡",  # Use an emoji or a link to an image
    layout="wide",  # Wide layout for better use of screen space
    initial_sidebar_state="expanded",
)



##### API Details for CO2 data

CARBON_INTENSITY_API_URL = 'https://api.electricitymap.org/v3/carbon-intensity/history'
CARBON_INTENSITY_TOKEN = 'ATSASQPg3AZYu'

def get_last_24_hours_data(zone="ES"):
    """
    Fetch the carbon intensity data for the last 24 hours for the specified zone.
    :param zone: Zone code for the API request (e.g., "ES" for Spain).
    :return: DataFrame containing datetime and carbon intensity values for the last 24 hours.
    """
    headers = {'auth-token': CARBON_INTENSITY_TOKEN}
    params = {'zone': zone}
    response = requests.get(CARBON_INTENSITY_API_URL, headers=headers, params=params)
    response.raise_for_status()
    
    data = response.json()
    print("API Response:", data)  # Log the API response
    
    if 'history' in data:
        history = data['history']
        last_24_hours = []
        now = datetime.now(timezone.utc)  # Use timezone-aware UTC datetime
        
        # Filter data for the last 24 hours
        for record in history:
            record_time = datetime.strptime(record['datetime'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            if now - record_time <= timedelta(hours=24):
                last_24_hours.append({
                    "Timestamp": record_time,
                    "Carbon_Intensity_(gCO2eq/kWh)": record['carbonIntensity']
                })
        
        # Create a DataFrame from the filtered data
        if last_24_hours:
            df = pd.DataFrame(last_24_hours)
            return df
        else:
            raise ValueError("No data found for the last 24 hours.")
    else:
        raise ValueError("No history data found in the API response.")

# Fetch and process the data
def fetch_and_process_data():
    try:
        CO2_df = get_last_24_hours_data()
        return CO2_df
    except Exception as e:
        print("Error:", e)
        return None

# Fetch the data outside the function
CO2_df = fetch_and_process_data()




# Date range to be shown in the dashboard (last 30 days) - this can be adjusted
default_start_date = (datetime.now() - timedelta(days=30)).date()
default_end_date = datetime.now().date()




###### Sidebar configurations
st.sidebar.header("⚙️ Dashboard Controls")

# Sidebar for dark mode toggle
st.sidebar.header("Accessibility Features")
#dark_mode = st.sidebar.checkbox("Enable Dark Mode 🌚")
dark_mode = st.sidebar.checkbox("Enable Dark Mode 🌚", value=False)

# Update plotly template based on the dark mode toggle
plotly_template = "plotly_dark" if dark_mode else "plotly"

# Define Plotly theme based on the dark mode toggle
if dark_mode:
    plotly_template = "plotly_dark"
    st.markdown(
        """
        <style>
        body {
            background-color: #2B2B2B;
            color: white;
        }
        .sidebar-content {
            background-color: #333333;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    plotly_template = "plotly"
    st.markdown(
        """
        <style>
        body {
            background-color: white;
            color: black;
        }
        .sidebar-content {
            background-color: #f0f0f0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Sidebar date inputs
start_date = st.sidebar.date_input("Start Date", value=default_start_date, min_value=default_start_date)
end_date = st.sidebar.date_input("End Date", value=default_end_date, min_value=start_date)

if start_date > end_date:
    st.sidebar.error("Start Date cannot be after End Date. Please adjust your selection.")

# Toggle for detailed analysis
#show_detailed_analysis = st.sidebar.checkbox("Show Detailed Analysis")

# Sidebar input for CO2 threshold
st.sidebar.markdown("### CO2 Emissions Control")
co2_threshold = st.sidebar.slider(
    "Set CO2 Emission Threshold (gCO2eq/kWh)", 
    min_value=0, 
    max_value=1000, 
    value=300, 
    step=10
)

# Graph customization
st.sidebar.markdown("### Customize Graphs")
line_color = st.sidebar.color_picker("Pick a Line Color", "#636EFA")
line_style = st.sidebar.radio("Line Style", options=["solid", "dash", "dot"], index=0)





# API Details for electricity prices
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
        st.subheader("REDUCING CO2 EMISSIONS WHILE CHARGING A LAPTOP")
        # Add tabs for organizing sections
        tab1, tab2, tab3 = st.tabs(["📈 Overview", "🔍 Detailed Analysis", "📊 Forecasts"])




        # Overview Tab
        with tab1:

            #Electricity Prices Section
            st.subheader("Electricity Prices Over the Selected Period")

            #Selected line color to the plot
            fig = px.line(data, x='Time', y='Price (€/MWh)', title='Spot Market Prices Over Time',
                          labels={'Price (€/MWh)': 'Price (€/MWh)', 'Time': 'Time'}, line_shape='linear', template=plotly_template)
            fig.update_traces(line=dict(color=line_color, dash=line_style))

            fig.update_layout(xaxis_title="Time", yaxis_title="Price (€/MWh)", title_x=0.5)
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("Show raw data"):
                st.dataframe(data)

            # CO2 Emissions Section            
            st.subheader("Latest Carbon Emissions Data")

            if CO2_df is not None:
                # Display the current threshold and status
                st.subheader("CO2 Emissions Threshold and Laptop Charging Status")
                st.write(f"Current CO2 Threshold: {co2_threshold} gCO2eq/kWh")
                
                # Add a column to indicate whether charging is allowed
                CO2_df['Charging_Status'] = CO2_df['Carbon_Intensity_(gCO2eq/kWh)'] < co2_threshold
                
                # Show a summary of the current charging status
                last_entry = CO2_df.iloc[-1]
                current_emission = last_entry['Carbon_Intensity_(gCO2eq/kWh)']
                is_charging = last_entry['Charging_Status']
                
                if is_charging:
                    st.success(f"Laptop will charge. Current CO2 emissions below threshold: {current_emission:.2f} gCO2eq/kWh")
                else:
                    st.error(f"Laptop will NOT charge. Current CO2 emissions above threshold: {current_emission:.2f} gCO2eq/kWh")
                
                # Visualize the threshold
                fig_threshold = px.line(
                    CO2_df, 
                    x='Timestamp', 
                    y='Carbon_Intensity_(gCO2eq/kWh)', 
                    title='Carbon Intensity with Charging Threshold',
                    labels={'Carbon_Intensity_(gCO2eq/kWh)': 'CO2 Intensity (gCO2eq/kWh)', 'Timestamp': 'Timestamp'},
                    template=plotly_template
                )
                fig_threshold.update_traces(line=dict(color=line_color, dash=line_style))

                fig_threshold.add_hline(y=co2_threshold, line_dash="dash", line_color="red", annotation_text="Threshold")
                st.plotly_chart(fig_threshold, use_container_width=True)

            else:
                st.error("Unable to load carbon intensity data.")



        # Detailed Analysis Tab
        with tab2:
            st.subheader("Detailed Analysis")
            last_week = data[data['Date'] >= (datetime.now().date() - timedelta(days=7))]
            daily_min = last_week.groupby('Date').apply(lambda x: x.loc[x['Price (€/MWh)'].idxmin()])
            st.markdown("### Lowest Electricity Prices Per Day (Last 7 Days)")
            st.dataframe(daily_min[['Date', 'Hour', 'Price (€/MWh)']])

            # Bar Chart: Average Prices Per Hour
            st.subheader("Average Prices Per Hour")
            avg_prices_per_hour = data.groupby('Hour')['Price (€/MWh)'].mean().reset_index()
            
            bar_chart = px.bar(
                avg_prices_per_hour, 
                x='Hour', 
                y='Price (€/MWh)', 
                title="Average Hourly Electricity Prices",
                labels={'Price (€/MWh)': 'Average Price (€/MWh)', 'Hour': 'Hour of Day'},
                template=plotly_template
            )
            bar_chart.update_traces(marker_color=line_color)
            bar_chart.update_layout(xaxis_title="Hour", yaxis_title="Average Price (€/MWh)", title_x=0.5)
            st.plotly_chart(bar_chart, use_container_width=True)


            # Analytics for CO2 Emissions
            st.subheader("CO2 Emissions Analysis")

            # Convert 'Timestamp' to datetime with timezone awareness (if not already done)
            CO2_df['Timestamp'] = pd.to_datetime(CO2_df['Timestamp']).dt.tz_convert('UTC')

            # Get the current time as a timezone-aware datetime
            now_utc = pd.Timestamp.now(tz='UTC')

            # Filter data for the last 24 hours
            last_24_hours = CO2_df[CO2_df['Timestamp'] >= (now_utc - pd.Timedelta(hours=24))]

            # Calculate analytics for the last 24 hours
            if not last_24_hours.empty:
                lowest_CO2 = last_24_hours['Carbon_Intensity_(gCO2eq/kWh)'].min()
                mean_CO2 = last_24_hours['Carbon_Intensity_(gCO2eq/kWh)'].mean()
                highest_CO2 = last_24_hours['Carbon_Intensity_(gCO2eq/kWh)'].max()

                # Display analytics
                st.subheader("CO₂ Emissions Analytics (Last 24 Hours)")
                st.write(f"**Lowest CO₂ Emission:** {lowest_CO2:.2f} gCO₂eq/kWh")
                st.write(f"**Mean CO₂ Emission:** {mean_CO2:.2f} gCO₂eq/kWh")
                st.write(f"**Highest CO₂ Emission:** {highest_CO2:.2f} gCO₂eq/kWh")
            else:
                st.write("No CO₂ data available for the last 24 hours.")

            # Bar chart for CO₂ emissions
            fig_CO2_analytics = px.bar(
                CO2_df,
                x='Timestamp',
                y='Carbon_Intensity_(gCO2eq/kWh)',
                title='Latest Carbon Emissions Data',
                labels={
                    'Carbon_Intensity_(gCO2eq/kWh)': 'Carbon Intensity (gCO₂eq/kWh)',
                    'Timestamp': 'Timestamp'
                },
                template="plotly_white"
            )
            fig_CO2_analytics.update_traces(marker_color=line_color)

            # Update layout
            fig_CO2_analytics.update_layout(
                xaxis_title="Timestamp",
                yaxis_title="Carbon Intensity (gCO₂eq/kWh)",
                title_x=0.5
            )

            # Display the plot
            st.plotly_chart(fig_CO2_analytics, use_container_width=True)


            

            #Comparison between two time periods
            st.subheader("Comparison between two time periods")

            # Sidebar inputs for comparison date ranges
            st.sidebar.header("🌀 Compare Time Periods")
            compare_start1 = st.sidebar.date_input("Start Date for Period 1", value=start_date, min_value=default_start_date)
            compare_end1 = st.sidebar.date_input("End Date for Period 1", value=end_date, min_value=compare_start1)

            compare_start2 = st.sidebar.date_input("Start Date for Period 2", value=start_date, min_value=default_start_date)
            compare_end2 = st.sidebar.date_input("End Date for Period 2", value=end_date, min_value=compare_start2)

            if compare_start1 > compare_end1 or compare_start2 > compare_end2:
                st.warning("Ensure start dates are before end dates for both periods.")
            
            else:
                # Filter data for the two periods
                data_period1 = data[(data['Date'] >= compare_start1) & (data['Date'] <= compare_end1)]
                data_period2 = data[(data['Date'] >= compare_start2) & (data['Date'] <= compare_end2)]

                # Add a label column for grouping
                data_period1['Period'] = 'Period 1'
                data_period2['Period'] = 'Period 2'

                # Combine both periods into a single DataFrame
                comparison_data = pd.concat([data_period1, data_period2])

                # Plot comparison graph
                comparison_fig = px.line(
                    comparison_data,
                    x='Time',
                    y='Price (€/MWh)',
                    color='Period',
                    title="Comparison of Electricity Prices Between Two Periods",
                    labels={'Price (€/MWh)': 'Price (€/MWh)', 'Time': 'Time'},
                    template=plotly_template
                )
                comparison_fig.update_layout(xaxis_title="Time", yaxis_title="Price (€/MWh)", title_x=0.5)
                st.plotly_chart(comparison_fig, use_container_width=True)

        # Forecast Tab
        with tab3:
            st.subheader("Expected Trend for the Next Day")
            
            # Fetch or simulate data for the next day
            now = datetime.now()
            next_day = (now + timedelta(days=1)).date()

            if now.hour >= 12:
                # Fetch next day's prices
                params_next_day = {
                    'start_date': f'{next_day}T00:00',
                    'end_date': f'{next_day}T23:59',
                    'time_trunc': 'hour'
                }
                response_next_day = requests.get(endpoint + get_archives, headers=headers, params=params_next_day)

                if response_next_day.status_code == 200:
                    next_day_data = response_next_day.json()
                    try:
                        # Check if the 'included' key has sufficient data
                        if 'included' in next_day_data and len(next_day_data['included']) > 1:
                            next_day_spot = next_day_data['included'][1]['attributes']['values']
                            next_day_prices = [d['value'] for d in next_day_spot]
                            next_day_times = [datetime.strptime(d['datetime'], "%Y-%m-%dT%H:%M:%S.%f%z") for d in next_day_spot]
                            next_day_df = pd.DataFrame({'Time': next_day_times, 'Price (€/MWh)': next_day_prices})
                        else:
                            st.warning("Prices for tomorrow are not yet available. Displaying synthetic data.")
                            next_day_prices = np.sin(np.linspace(0, 2 * np.pi, 24)) + 50
                            next_day_times = pd.date_range(next_day, periods=24, freq='H')
                            next_day_df = pd.DataFrame({'Time': next_day_times, 'Price (€/MWh)': next_day_prices})
                    except KeyError:
                        st.error("Unexpected response structure from the API. Displaying synthetic data.")
                        next_day_prices = np.sin(np.linspace(0, 2 * np.pi, 24)) + 50
                        next_day_times = pd.date_range(next_day, periods=24, freq='H')
                        next_day_df = pd.DataFrame({'Time': next_day_times, 'Price (€/MWh)': next_day_prices})
                else:
                    st.warning("Failed to fetch prices for the next day. Displaying synthetic data.")
                    next_day_prices = np.sin(np.linspace(0, 2 * np.pi, 24)) + 50
                    next_day_times = pd.date_range(next_day, periods=24, freq='H')
                    next_day_df = pd.DataFrame({'Time': next_day_times, 'Price (€/MWh)': next_day_prices})
            else:
                st.info("Prices for the next day are not available yet. Displaying synthetic data.")
                next_day_prices = np.sin(np.linspace(0, 2 * np.pi, 24)) + 50
                next_day_times = pd.date_range(next_day, periods=24, freq='H')
                next_day_df = pd.DataFrame({'Time': next_day_times, 'Price (€/MWh)': next_day_prices})

            # Display next day's trend
            #st.markdown("### Expected Trend for the Next Day")
            next_day_fig = px.line(next_day_df, x='Time', y='Price (€/MWh)', title="Expected Prices for Tomorrow",
                                   template=plotly_template)
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
