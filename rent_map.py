import mapclassify
import plotly.express as px
import folium
import pandas as pd
import matplotlib
import geopandas as gpd
import streamlit as st
from streamlit_folium import st_folium
from lga_data import *
# 'folium', 'matplotlib' and 'mapclassify

data_link = 'data/Rent-tables-December-2022-quarter.xlsx'
shape_path = 'data/POA_2021_AUST_GDA94_SHP/POA_2021_AUST_GDA94.shp'

data= pd.read_excel(data_link, sheet_name='Postcode', skiprows=range(8))

# rename columns
data.rename(columns = {'Postcode':'postcode',
                       'Dwelling Types':'types',
                       'Number of Bedrooms':'rooms',
                       'Median Weekly Rent for New Bonds\n$':'rent_median',
                       'Quarterly change in Median Weekly Rent':'quarter_change_rent',
                       'Annual change in Median Weekly Rent':'annual_change_rent'},
            inplace = True)

# lga_postcode is imported from lga_data.py
all_postcodes = list(set([value for values in lga_postcodes.values() for value in values]))
post_groups = list(lga_postcodes.keys())

postcode_Canterbury = [2191,2192,2193,2194,2206] # deafault values of selected postcodes
num_rooms = list(set(data['rooms']))
dwelling_types = list(set(data['types']))

# Initialization
if 'default_postcodes' not in st.session_state:
  st.session_state['default_postcodes'] = postcode_Canterbury #postcode_Canterbury 

if 'default_regions' not in st.session_state:
  st.session_state['default_regions'] = ['Canterbury'] #postcode_Canterbury 

st.set_page_config(page_title="Sydney rent map", layout="wide")


st.sidebar.header('Set postcodes')
with st.sidebar.form(key= 'postcode_form'):
  selected_postcodes = st.multiselect(
      label = 'Choose postcodes you want to know the median rents in those area:',
      options = all_postcodes,
      key = 'selected_postcodes', 
      default = st.session_state['default_postcodes'])
  
  submit_postcode = st.form_submit_button(label='Set postcodes')  
  
  if submit_postcode:
    st.session_state['default_postcodes'] = selected_postcodes      

st.sidebar.header('Or select postcodes based on specific regions:')
with st.sidebar.form(key='region_form'):
  selected_regions = st.multiselect(
      label = 'Choose areas you are interested in:',
     options = post_groups,
     key = 'region',
     default = st.session_state['default_regions']
     )
  
  submit_region = st.form_submit_button(label='Set regions')
  
  if submit_region:
    postcodes_all = []
    chosen_groups = selected_regions #st.session_state['default_regions'] 
    for group in chosen_groups:
      postcodes = lga_postcodes[group] 
      postcodes_all.extend(postcodes)
    selected_postcodes = postcodes_all 
    st.session_state['default_postcodes'] = postcodes_all
    st.session_state['default_regions'] = selected_regions  

st.sidebar.header('Select dwelling types and number of bedrooms')
with st.sidebar.form(key='dwell_form'):
  d_type = st.selectbox(label = 'What kind of accommodation you are looking for?', 
                   options = dwelling_types
                   )
  n_room = st.selectbox(label = 'How many rooms are needed?', 
                   options = num_rooms
                   )
  submit_dwell = st.form_submit_button(label='Set dwelling styles')

@st.cache_data
def data_filter(data, postcode, types, rooms):
  filter_postcodes = data['postcode'].isin(postcode)
  filter_type = data['types']==types #data['types'].isin(types) #data['types']==types 
  filter_room = data['rooms']==rooms #data['rooms'].isin(rooms) #data['rooms']==rooms #	
  all_filters = filter_postcodes & filter_type & filter_room 
  selected_data = data[all_filters]

  df_rent = selected_data[['postcode', 'types', 'rooms','rent_median','quarter_change_rent','annual_change_rent']]
  df_rent['rent_median'] = pd.to_numeric(df_rent['rent_median'], errors='coerce')
  df_rent['quarter_change_rent'] = pd.to_numeric(df_rent['quarter_change_rent'], errors='coerce')
  df_rent['annual_change_rent'] = pd.to_numeric(df_rent['annual_change_rent'], errors='coerce')

  return df_rent

@st.cache_data
def get_map_data(df_rent, shape_path):
  region = gpd.read_file(shape_path)
  region['POA_CODE21'] = pd.to_numeric(region['POA_CODE21'], errors='coerce')
  region.rename(columns = {'POA_CODE21':'postcode'}, inplace = True)
  region.drop(region.columns.difference(['postcode', 'geometry']), axis=1, inplace=True)
  
  # Merge gpd dataframe with pandas dataframe
  region_map = region.merge(df_rent, on='postcode')
  e_col = region_map.pop('geometry')
  region_map.insert(1, 'geometry', e_col)
  return region_map

df_rent = data_filter(data, selected_postcodes, d_type, n_room)
df_map = get_map_data(df_rent, shape_path)


st.title('Sydney rent map')
st.header("A rent map based on postcodes of Sydney resgion")
st.markdown('This page is for visualization of the median rent of the great Sydney area. I tried to make this map because only the visualization of median rent based on local government areas (which looks really beautiful) can be found at the the office website of NSW. But I am trying to look a bit more closer.')
st.markdown('Dwellings rental data by LGA/postcodes for December 2022 quarter can be downloaded from https://www.facs.nsw.gov.au/resources/statistics/rent-and-sales/dashboard .')

tab_full, tab_heatmap = st.tabs(['With actual map', "Heatmap only"])

with tab_full:
    st.header('Map with geographic information')
    
        
    # full map
    try:
      #
      m = df_map.explore(column='rent_median',  # make choropleth based on "BoroName" column
                 cmap ='Purples',
                 legend=True, # show legend
                 k=10, # use 10 bins
                 legend_kwds=dict(colorbar=True) # do not use colorbar
                 )
      st_folium(m)
    except:
      st.write('Something wrong, please reset the conditions')
    
with tab_heatmap:
    st.header('Heatmap of rents for choosing areas')

    # Heatmap
    try:
      #
      fig = px.choropleth(df_map,
                  geojson=df_map.geometry, 
                  locations=df_map.index,
                  hover_name = 'postcode',
                  color='rent_median', 
                  color_continuous_scale = 'Purples'
                  )
      fig.update_geos(fitbounds="locations", visible=False)
      fig
    except: 
      st.write('Something wrong, please reset the conditions')

  
st.header("Reference")
st.markdown('There were already similar analyses conducted by Tariq Munir and walthersy@Github (and his colleadgues). Codes and instructions could be found via the following links:')
st.markdown('1. https://towardsdatascience.com/exploring-greater-sydney-suburbs-f2bf1562988e  ')
st.markdown('2. https://github.com/Timun01/IBM-Capstone-Project')
st.markdown('3. https://github.com/walthersy/NSW-house-price')

st.markdown('Many thnks to their kindly sharing.')