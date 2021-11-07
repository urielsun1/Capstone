# -*- coding: utf-8 -*-
"""
Created on Sun Oct 17 17:51:55 2021

@author: Yi Sun
"""
import streamlit as st
import pandas as pd
import numpy as np
import dateutil
import datetime
import pydeck as pdk
import plotly.express as px
import folium
import calendar
import time
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static


# SETTING PAGE CONFIG TO WIDE MODE
st.set_page_config(layout="wide")

DATA_URL = "Motor_Vehicle_Collisions_Crashes_NYPD.csv"


st.title("🗽NYC Motor Vehicle Collisions🌇")
st.markdown("Motor Vehicle Collisions 💥🚗 is one of the leading causes of death globally. In NYC, hundreds of car accidents happens in every single day.")
st.markdown("This web app was built to allow users to map past motor vehicle collision events in NYC, visualize accident-prone areas on the map, investigate the temporal pattern of collisions "
            "and examine what factors might be correlated with vehicle collisions.")
st.markdown("Dataset is motor vehicle collision events reported by NYPD from 1/7/2012 to 2/5/2021")



@st.cache(persist=True)
def load_data(url):
    data = pd.read_csv("Motor_Vehicle_Collisions_Crashes_NYPD.csv", low_memory = False)
    data['CRASH DATE'] = data['CRASH DATE'].apply(dateutil.parser.parse, dayfirst=True)
    #data['CRASH DATETIME'] = data['CRASH DATE'] + " " +data['CRASH TIME']
    #data['CRASH DATETIME'] = pd.to_datetime(data['CRASH DATETIME'], format = '%m/%d/%Y %H:%M')
    data['hour'] = pd.DatetimeIndex(data['CRASH TIME']).hour
    data['year'] = pd.DatetimeIndex(data['CRASH DATE']).year
    data['month'] = pd.DatetimeIndex(data['CRASH DATE']).month
    data['weekday'] = pd.to_datetime(data['CRASH DATE']).dt.day_name()
    data['season'] = (data['month']%12 + 3)//3
    seasons = {1: '1 Winter', 2: '2 Spring', 3: '3 Summer', 4: '4 Autumn'}
    data['season_name'] = data['season'].map(seasons)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis="columns", inplace=True)
    df = data.dropna(subset=['latitude', 'longitude'])
    return df

df = load_data(DATA_URL)


# Visualize Motor Vehicle Collisions happened in NYC (2012-2021)
st.header("Motor Vehicle Collisions Happened in NYC")
st.markdown("Select the date range you want to visualize. You can select specific collision type as well. For better and faster performance, please choose date range within a year when visualizing all collisions.")

row1_1, row1_2 = st.columns((1,1))
with row1_1:
    select = st.selectbox('Collision Type: Is anybody injured or killed?', ['All Collisions', 'Collisions with Injuries', 'Collisions with Death'], key ="1")

min_date = datetime.date(2012,1,7)
max_date = datetime.date(2021,2,2)
with row1_2:
    start_date, end_date = st.date_input('Start Date - End Date :', value=(datetime.date(2020,10,1), datetime.date(2021,1,1)), min_value=min_date, max_value=max_date)

if start_date < end_date:
    pass
else:
    st.write('Error: End date must fall after start date.')
            
if select == 'All Collisions':
    filtered2 = df[(df['crash date'].dt.date > start_date) & (df['crash date'].dt.date <= end_date)]

elif select == 'Collisions with Injuries':
    filtered2 = df[(df['crash date'].dt.date > start_date) & (df['crash date'].dt.date <= end_date) & (df['number of persons injured'] > 0)]

else:
    filtered2 = df[(df['crash date'].dt.date > start_date) & (df['crash date'].dt.date <= end_date) & (df['number of persons killed'] > 0)]

#Create Cluster Maps for Selected Collisions
if filtered2.empty:
    st.write('No Collisions of this type were recorded during this date range.')
else: 
    map2 = folium.Map(location=[40.7, -73.9], zoom_start = 10)
    locations = list(zip(filtered2["latitude"].values, filtered2["longitude"].values))
    marker_cluster = MarkerCluster(locations).add_to(map2)
    folium_static(map2)


# Visualize Motor Vehicle Collisions happened at given hour of day
st.header("Motor Vehical Collisions Happened at Different Hour of Day")
st.markdown("Select the hour of the day you want to visualize. Collision events are grouped into hexagon with a default radius of 30 meters. You can change the radius size for your need")

row2_1, row2_2 = st.columns((1,1))
with row2_1:
    hour = st.slider("Select the specific hour:", 0, 23)
with row2_2:
    radius = st.slider("Select the radius (in meters) for the Hexagon:", 30, 500, step = 10, key = '3')
df_hour = df[df['hour'] == hour]

                    
st.markdown("Motor vehicle collisions between %i:00 and %i:00" % (hour, (hour + 1) % 24))

midpoint = (np.average(df["latitude"]), np.average(df["longitude"]))
st.write(pdk.Deck(
    map_style="mapbox://styles/mapbox/streets-v10",
    initial_view_state={
        "latitude": midpoint[0],
        "longitude": midpoint[1],
        "zoom": 11,
        "pitch": 50,
    },
    layers=[
        pdk.Layer(
        "HexagonLayer",
        data= df_hour[['hour', 'latitude', 'longitude']],
        get_position=["longitude", "latitude"],
        auto_highlight=True,
        radius=radius,
        extruded=True,
        pickable=True,
        elevation_scale=4,
        elevation_range=[0, 800],
        ),
    ],
    
))


#Animation Visualization of Temporal and Spatial Pattern of Collisions in a given day
st.header("Motor Vehical Collisions Temporal & Spatial Pattern Animation")
st.markdown("This animation shows yearly 24-hour spatial pattern of NYC motor vehicle collisions from 2013 to 2020. You can change the hexagon radius for your need")
df2 = df[['year', 'hour', 'latitude', 'longitude']].dropna(how = 'any')
layer = pdk.Layer(
        "HexagonLayer",
        data=df2,
        get_position=["longitude", "latitude"],
        auto_highlight=True,
        radius=50,
        extruded=True,
        pickable=True,
        elevation_scale=4,
        elevation_range=[0, 500],
        )


# Create the deck.gl map
r = pdk.Deck(
    layers = [layer],
    initial_view_state={
        "latitude": midpoint[0],
        "longitude": midpoint[1],
        "zoom": 11,
        "pitch": 50,
    },
    map_style="mapbox://styles/mapbox/streets-v10",
    )

# Create a subheading to display current hour
subheading = st.subheader("")
# Render the deck.gl map in the Streamlit app as a Pydeck chart 
map = st.pydeck_chart(r)
# Update the maps and the subheading each hour
for i in range(2013, 2020, 1):
    temp = df2[df2['year'] == i]
    for j in range(0, 24, 1):
        layer.data = temp[temp['hour'] == j]
        r.update()
        map.pydeck_chart(r)
        subheading.subheader("Vehicle collisions between %i:00 and %i:00 in %i" % (j, (j + 1) % 24, i))
        time.sleep(0.5)



# Visualize Motor Vehicle Collisions happened at specific month
st.header("Motor Vehical Collisions Happened in Specific Month")
st.markdown("Select the month you want to visualize. Collision events are grouped into hexagon with a default radius of 30 meters. You can change the radius size for your need")                             
row3_1, row3_2 = st.columns((1,1))
with row3_1:
    month = st.slider("Select the specific month:", 1, 12)
with row3_2:
    radius = st.slider("Select the radius (in meters) for the Hexagon:", 30, 500, step = 10, key = '4')
df_month = df[df['month'] == month]

month_name = calendar.month_name[month]
month_subheading = f"Motor Vehicle Collisions in {month_name}"                    
st.markdown(month_subheading)

midpoint = (np.average(df["latitude"]), np.average(df["longitude"]))
st.write(pdk.Deck(
    map_style="mapbox://styles/mapbox/streets-v10",
    initial_view_state={
        "latitude": midpoint[0],
        "longitude": midpoint[1],
        "zoom": 11,
        "pitch": 50,
    },
    layers=[
        pdk.Layer(
        "HexagonLayer",
        data= df_month[['month', 'latitude', 'longitude']],
        get_position=["longitude", "latitude"],
        auto_highlight=True,
        radius=radius,
        extruded=True,
        pickable=True,
        elevation_scale=4,
        elevation_range=[0, 800],
        ),
    ],
    
))
    

st.header("Most Dangerous Streets in NYC")
st.markdown("Top 10 most dangerous streets of each collision type. Select specific affected classes to see the most dangerous streets for motorist, cyclists and pedestrains, repectively.")
row4_1, row4_2 = st.columns((1,1))
with row4_1:
    select_collisions = st.selectbox('Collision Type: Is anybody injured or killed?', ['All Collisions', 'Collisions with Injuries', 'Collisions with Death'], key ="5")
with row4_2:
    select_class = st.selectbox('Affected class', ['All', 'Motorists', 'Cyclists', 'Pedestrians'])

if select_collisions == 'Collisions with Injuries':
    if select_class == 'Pedestrians':
        filtered4 = df.groupby(['on street name'])['number of pedestrians injured'].sum().reset_index()
        st.write(filtered4[filtered4['number of pedestrians injured'] >= 1][["on street name", "number of pedestrians injured"]].sort_values(by=['number of pedestrians injured'], ascending=False).dropna(how="any")[:10])
    
    elif select_class == 'Cyclists':
        filtered4 = df.groupby(['on street name'])['number of cyclist injured'].sum().reset_index()
        st.write(filtered4[filtered4['number of cyclist injured'] >= 1][["on street name", "number of cyclist injured"]].sort_values(by=['number of cyclist injured'], ascending=False).dropna(how="any")[:10])
    
    elif select_class == 'Motorists':
        filtered4 = df.groupby(['on street name'])['number of motorist injured'].sum().reset_index()
        st.write(filtered4[filtered4['number of motorist injured'] >= 1][["on street name", "number of motorist injured"]].sort_values(by=['number of motorist injured'], ascending=False).dropna(how="any")[:10])
    
    else:
        filtered4 = df.groupby(['on street name'])['number of persons injured'].sum().reset_index()
        filtered4['number of persons injured'] = filtered4['number of persons injured'].fillna(0).astype(int)
        st.write(filtered4[filtered4['number of persons injured'] >= 1][["on street name", "number of persons injured"]].sort_values(by=['number of persons injured'], ascending=False).dropna(how="any")[:10])
        
elif select_collisions == 'Collisions with Death':
    if select_class == 'Pedestrians':
        filtered4 = df.groupby(['on street name'])['number of pedestrians killed'].sum().reset_index()
        st.write(filtered4[filtered4['number of pedestrians killed'] >= 1][["on street name", "number of pedestrians killed"]].sort_values(by=['number of pedestrians killed'], ascending=False).dropna(how="any")[:10])
    
    elif select_class == 'Cyclists':
        filtered4 = df.groupby(['on street name'])['number of cyclist killed'].sum().reset_index()
        st.write(filtered4[filtered4['number of cyclist killed'] >= 1][["on street name", "number of cyclist killed"]].sort_values(by=['number of cyclist killed'], ascending=False).dropna(how="any")[:10])
    
    elif select_class == 'Motorists':
        filtered4 = df.groupby(['on street name'])['number of motorist killed'].sum().reset_index()
        st.write(filtered4[filtered4['number of motorist killed'] >= 1][["on street name", "number of motorist killed"]].sort_values(by=['number of motorist killed'], ascending=False).dropna(how="any")[:10])
    
    else:
        filtered4 = df.groupby(['on street name'])['number of persons killed'].sum().reset_index()
        filtered4['number of persons killed'] = filtered4['number of persons killed'].fillna(0).astype(int)
        st.write(filtered4[filtered4['number of persons killed'] >= 1][["on street name", "number of persons killed"]].sort_values(by=['number of persons killed'], ascending=False).dropna(how="any")[:10])

else:
    filtered4 = df.groupby(['on street name']).size().reset_index(name='collision counts')
    #st.write(filtered4[['on street name', 'collision counts']])    
    st.write('Below are the streets with the most collisions, affected class is not in consideration in this case')
    st.write(filtered4[['on street name', 'collision counts']].sort_values(by=['collision counts'], ascending=False).dropna(how="any")[:10])
  
    
# Visualize how different factors affect collisions
st.header("What can have effects on Collisions?")
st.markdown("Here you can see the top contributing factors that caused the collisions according to accident report. You can also investigate which hour of the day, day of the week or month have the most collisions happened. You can also select collision type.")
 
row5_1, row5_2 = st.columns((1,1))
with row5_1:
    select_collisions2 = st.selectbox('Collision Type: Is anybody injured or killed?', ['All Collisions', 'Collisions with Injuries', 'Collisions with Death'], key ="6")
with row5_2:    
    select_factor = st.selectbox('Select the factor of your interest', ['month', 'weekday', 'hour', 'contributing factor'], key ="7")

if select_collisions2 == 'Collisions with Injuries':
    filtered5 = df[df['number of persons injured'] > 0]
elif select_collisions2 == 'Collisions with Death':
    filtered5 = df[df['number of persons killed'] > 0]
else:
    filtered5 = df
    
if select_factor == 'contributing factor':
    a = filtered5[['contributing factor vehicle 1','contributing factor vehicle 2', 'contributing factor vehicle 3', 'contributing factor vehicle 4']].apply(pd.Series.value_counts).fillna(0).astype(int)
    a['counts'] = a['contributing factor vehicle 1'] + a['contributing factor vehicle 2'] + a['contributing factor vehicle 3'] + a['contributing factor vehicle 4']
    b = a.sort_values(by='counts')[:].tail(30)
    fig = px.bar(b, y=b.index, x = 'counts', orientation = 'h', labels ={'index':''})
    fig.update_yaxes(tickmode = 'linear')
    fig.update_layout(autosize=False, width=1800, height=900)
    st.write(fig)
else:
    def plot_factor (select_factor):
        temp = filtered5.groupby([select_factor]).size().reset_index(name = 'counts')
        d = temp.sort_values(by=['counts'], ascending = False)
        fig = px.bar(d, x=select_factor, y ='counts')
        fig.update_xaxes(tickmode = 'linear')
        fig.update_layout(autosize=False, width=800, height=500)
        return fig
 
    fig = plot_factor(select_factor)
    st.write(fig)
    


    
    