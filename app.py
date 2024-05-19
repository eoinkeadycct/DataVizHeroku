#!/usr/bin/env python
# coding: utf-8

# # Data Visualization CA2
# 
# sba23031
# 
# Eoin Keady
# 
# https://github.com/CCT-Dublin/data-visualization-pt-ca2-eoinkeadycct

# In[1]:


import pandas as pd
from dash import Dash, dcc, html, Input, Output, clientside_callback
import plotly.express as px
import dash_bootstrap_components as dbc


# In[2]:


# To read the excel file

# pip install openpyxl


# # Reading in data

# In[3]:


xlsx_online = 'mye22final.xlsx'

# Load in the last sheet which is machine learning readable
df = pd.read_excel(xlsx_online, sheet_name='MYEB1')

# Load the density of regions with no age or gender from sheet MYE5. Keep it for use later
df_density_original = pd.read_excel(xlsx_online, sheet_name='MYE5', skiprows=7)

#Merge the the two sheets so we have density for each gender and age.
df_density = df_density_original[['Code', 'Area (sq km)', 'Estimated Population mid-2022', '2022 people per sq. km', 'Estimated Population mid-2011',  '2011 people per sq. km']]
df_density.columns = ['code', 'area_sq_km', 'population_2022', 'density_2022', 'population_2011', 'density_2011']

# Merge the datasets on 'code'
df = pd.merge(df, df_density[['code', 'area_sq_km']], on='code', how='left')

# Calculate population densities
df['density_2011'] = df['population_2011'] / df['area_sq_km']
df['density_2022'] = df['population_2022'] / df['area_sq_km']


# In[4]:


df_density_original.head()


# In[5]:


df.head()


# In[6]:


df.shape


# # GeoNames file

# GeoNames - https://www.geonames.org/export/
# 
# GeoNames is a geographical database all countries. 
# 
# The GB_Full.txt file was retrieved from here - http://download.geonames.org/export/zip/
# 
# This contained coordinates within the United Kingdom so I merged this dataset with the existing one I have by joinging on the 'code' column

# In[7]:

# df_merged.to_csv('MergedDensityCoordinates.csv')

df_merged = pd.read_csv('MergedDensityCoordinates.csv')




# In[19]:


df_merged.shape


# # Dashboard

# ## Constants

# In[64]:


gender_dict = { "M": "Male", "F": "Female"}

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "right": 10,
    "bottom": 0,
    "width": "20%",
    "padding": "20px 10px",
    "background-color": "#f8f9fa",
    "z-index": "1",
}

CONTENT_STYLE = {
    "margin-left": "22%",
    "padding": "20px 10px",
}


# # Theme - LUX

# In[65]:


# Using LUX as I thought it was clean, simple and handy to use as its one of the given themes.

# I did overwrtie the font styling in ./assets/custom.css as I think Arial is more common and better of people who are visually imparied

app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])


# ## Filters

# In[66]:


charts_sidebar = html.Div(
    [
        html.P("Filters"),
        html.Hr(),
        html.Label("Select region:"),
        dcc.Dropdown(
            id='region-dropdown',
            options=[{'label': name, 'value': name} for name in df['name'].unique()],
            value='County Durham',
            clearable=False,
            style={'width': '100%'},
            searchable=True
        ),
        html.Br(),
        html.Label("Select year:"),
        dcc.Dropdown(
            id='year-dropdown',
            options=[
                {'label': '2011', 'value': 'density_2011'},
                {'label': '2022', 'value': 'density_2022'}
            ],
            value='density_2011',
            clearable=False,
            style={'width': '100%'}
        ),
        html.Br(),
        html.Label("Select gender:"),
        dcc.Dropdown(
            id='gender-dropdown',
            options=[
                {'label': 'Male', 'value': 'M'},
                {'label': 'Female', 'value': 'F'}
            ],
            value='M',
            clearable=False,
            style={'width': '100%'}
        ),
    ],
    style=SIDEBAR_STYLE,
)

map_sidebar = html.Div(
    [
        html.P("Filters"),
        html.Hr(),
        html.Label("Select Year:"),
        dcc.Dropdown(
            id='map-year-dropdown',
            options=[
                {'label': '2011', 'value': '2011 people per sq. km'},
                {'label': '2022', 'value': '2022 people per sq. km'}
            ],
            value='2011 people per sq. km',
            clearable=False,
            style={'width': '100%'}
        ),
    ],
    style=SIDEBAR_STYLE,
)

charts_content = html.Div(
    [
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='total-density-comparison'),
                dcc.Graph(id='density-by-age'),
                dcc.Graph(id='density-comparison')
            ])
        ])
    ],
    style=CONTENT_STYLE,
)

map_content = html.Div(
    [
        dcc.Graph(id='density-map')
    ],
    style=CONTENT_STYLE,
)

app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='Graphs', children=[
            charts_sidebar,
            charts_content
        ]),
        dcc.Tab(label='Interactive Map', children=[
            map_sidebar,
            map_content
        ]),
    ])
])

@app.callback(
    Output('density-by-age', 'figure'),
    [Input('region-dropdown', 'value'),
     Input('year-dropdown', 'value'),
     Input('gender-dropdown', 'value')]
)
def update_density_by_age(selected_region, selected_year, selected_gender):
    filtered_df = df[(df['name'] == selected_region) & (df['sex'] == selected_gender)]
    fig = px.bar(filtered_df,
                 x='age',
                 y=selected_year,
                 title=f'Population Density by Age in {selected_year[-4:]} for {gender_dict[selected_gender]}',
                 labels={
                      'age': 'Age', 
                      'density_2011': 'Density (per square kilometer)', 
                      'density_2022': 'Density (per square kilometer)'
                  })
    fig.update_traces(hoverinfo='y', marker=dict(color='LightSkyBlue'))
    return fig


# Density comparison by age and gender
@app.callback(
    Output('density-comparison', 'figure'),
    [Input('region-dropdown', 'value'),
     Input('gender-dropdown', 'value')]
)
def update_density_comparison(selected_region, selected_gender):
    filtered_df = df[(df['name'] == selected_region) & (df['sex'] == selected_gender)]

    plot_df = filtered_df.rename(columns={
        'density_2011': 'Density 2011',
        'density_2022': 'Density 2022'
    })
    fig = px.line(plot_df,
                  x='age',
                  y=['Density 2011', 'Density 2022'],
                  title=f'Population Density Comparison 2011 vs 2022 for {gender_dict[selected_gender]}',
                  labels={
                      'age': 'Age'
                  })
    fig.update_traces(
        hovertemplate='Age: %{x}<br>Density: %{y:.2f}<extra></extra>'
    )
        
    return fig


# Map
@app.callback(
    Output('density-map', 'figure'),
    [Input('map-year-dropdown', 'value')]
)
def update_density_map(selected_year):
    fig = px.scatter_mapbox(
        df_merged.dropna(subset=['latitude', 'longitude']),
        lat='latitude',
        lon='longitude',
        size=selected_year,
        color=selected_year,
        hover_name='Name',
        hover_data=['2011 people per sq. km', '2022 people per sq. km'],
        title=f'Population Density Map for {selected_year[-4:]}',
        size_max=15,
        zoom=5
    )
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig


# Total comparison
@app.callback(
    Output('total-density-comparison', 'figure'),
    [Input('region-dropdown', 'value')]
)
def update_total_density_comparison(selected_region):
    filtered_df = df[df['name'] == selected_region]
    total_density_2011 = filtered_df['density_2011'].mean()
    total_density_2022 = filtered_df['density_2022'].mean()
    
    comparison_df = pd.DataFrame({
        'Year': ['2011', '2022'],
        'Total Density': [total_density_2011, total_density_2022]
    })
    
    fig = px.bar(comparison_df,
                 x='Year',
                 y='Total Density',
                 color='Year',
                 color_discrete_map={'2011': 'blue', '2022': 'orange'},
                 title=f'Total Population Density Comparison for {selected_region} (2011 vs 2022)',
                 labels={'Total Density': 'Density (per square kilometer)'},)
    return fig

def update_figure_template(switch_on):
    template = pio.templates["minty"] if switch_on else pio.templates["minty_dark"]
    patched_figure = Patch()
    patched_figure["layout"]["template"] = template
    return patched_figure

if __name__ == '__main__':
    app.run_server(debug=True)


# In[ ]:





# In[ ]:





# In[ ]:




