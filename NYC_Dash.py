from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd

# Initialize Dash app with suppress_callback_exceptions
app = Dash(__name__, suppress_callback_exceptions=True)

# Volume Dataset
csv_file_path = r"E:\Dashboard\combined 3\Automated_Traffic_Volume_Counts.csv"

df = pd.read_csv(csv_file_path)
df = df[df['Yr'].between(2017, 2022)]
df = df.dropna(subset=['WktGeom', 'Yr', 'HH'])

from pyproj import Transformer
from shapely import wkt
transformer = Transformer.from_crs('epsg:2263', 'epsg:4326', always_xy=True)

def convert_wkt_to_lat_lon(wkt_str):
    if pd.notnull(wkt_str):
        try:
            point = wkt.loads(wkt_str)
            longitude, latitude = transformer.transform(point.x, point.y)
            return latitude, longitude
        except Exception:
            return None, None
    return None, None

df[['Latitude', 'Longitude']] = df['WktGeom'].apply(lambda x: pd.Series(convert_wkt_to_lat_lon(x)))
df = df.dropna(subset=['Latitude', 'Longitude'])
df_aggregated = df.groupby(['Yr', 'HH', 'Latitude', 'Longitude']).agg({'Vol': 'mean'}).reset_index()

# Volume Options
all_years = sorted(df_aggregated['Yr'].unique())
all_hours = sorted(df_aggregated['HH'].unique())
global_min_vol = df_aggregated['Vol'].min()
global_max_vol = df_aggregated['Vol'].max()

# Pre-Saved Maps
bus_map_file = "bus_routes_map.html"
commute_map_file = "commute_map.html"

# App Layout
app.layout = html.Div([
    html.H1("NYC Traffic Visualization", style={'textAlign': 'center'}),
    dcc.Dropdown(
        id='main-dropdown',
        options=[
            {'label': 'Volume', 'value': 'vol'},
            {'label': 'Bus', 'value': 'bus'},
            {'label': 'Commute', 'value': 'commute'}
        ],
        value='vol',
        clearable=False,
        style={'width': '50%', 'margin': '0 auto'}
    ),
    html.Div(id='dynamic-content')
])

@app.callback(
    Output('dynamic-content', 'children'),
    Input('main-dropdown', 'value')
)
def update_content(option):
    if option == 'vol':
        # Volume option content
        return html.Div([
            html.Div([
                html.Label("Select Year:"),
                dcc.Dropdown(
                    id='year-dropdown',
                    options=[{'label': str(year), 'value': year} for year in all_years],
                    value=all_years[0],
                    clearable=False
                )
            ], style={'width': '45%', 'display': 'inline-block'}),
            html.Div([
                html.Label("Select Hour:"),
                dcc.Dropdown(
                    id='hour-dropdown',
                    options=[{'label': f'{hour}:00', 'value': hour} for hour in all_hours],
                    value=all_hours[0],
                    clearable=False
                )
            ], style={'width': '45%', 'display': 'inline-block', 'marginLeft': '10px'}),
            dcc.Graph(id='density-map')
        ])
    elif option == 'bus':
        # Bus option content
        return html.Div([
            html.Label("Bus Map"),
            html.Iframe(
                id="bus-map",
                srcDoc=open(bus_map_file, "r").read(),
                width="100%",
                height="600px"
            )
        ])
    elif option == 'commute':
        # Commute option content
        return html.Div([
            html.Label("Commute Map"),
            html.Iframe(
                id="commute-map",
                srcDoc=open(commute_map_file, "r").read(),
                width="100%",
                height="600px"
            )
        ])
    return html.Div("Select an option from the dropdown.")

@app.callback(
    Output('density-map', 'figure'),
    [Input('year-dropdown', 'value'),
     Input('hour-dropdown', 'value')],
    prevent_initial_call=True
)
def update_volume_map(selected_year, selected_hour):
    # Update Volume map
    filtered_df = df_aggregated[(df_aggregated['Yr'] == selected_year) & (df_aggregated['HH'] == selected_hour)]
    fig = px.scatter_mapbox(
        filtered_df,
        lat='Latitude',
        lon='Longitude',
        color='Vol',
        size='Vol',
        size_max=15,
        zoom=9,
        center=dict(lat=40.7128, lon=-74.0060),
        color_continuous_scale=[[0, "lightgreen"], [0.25, "green"], [0.5, "yellow"], [0.75, "orange"], [1, "red"]],
        range_color=(global_min_vol, global_max_vol),
        mapbox_style="carto-positron",
        hover_name='Vol'
    )
    return fig

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8055)

