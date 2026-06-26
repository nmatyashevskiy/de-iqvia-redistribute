import streamlit as st
import plotly.express as px
import pandas as pd
import io
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestCentroid
from sklearn.metrics import DistanceMetric
import json
import geopandas as gpd

APP_TITLE = "Distribution of territories"


@st.cache_data
def display_map(df, FSR, territory):
    if territory == []:
        df_1 = df
        zoom_var = 5
        gj = st.session_state.geojson_data_land
    else:
        df_1 = df[df['Territory'].isin(territory)]
        zoom_var = 7
        gj = st.session_state.geojson_data_kreis
    
    lat_center = (df_1['Lat'].max() + df_1['Lat'].min())/2
    lon_center = (df_1['Lon'].max() + df_1['Lon'].min())/2

    fig1 = px.scatter_map(
        df_1,
        lat='Lat',
        lon='Lon',
        color='Territory', # 'Global Region',
        hover_name='Territory',
        hover_data={'Brick Name': True,
                    '# Accounts': True,
                    'Tier1': True,
                    'Tier2': True,
                    'Territory': False,
                    'Brick_code': False,
                    'Lon': False,
                    'Lat': False},
        #mapbox_style="carto-positron",
        size='# Accounts',
        size_max=20,
        center={'lat': lat_center, 'lon': lon_center},
        zoom=zoom_var,
        opacity=1)
    fig1.update_traces(
        marker={"sizemode": "area"},
        selected={"marker":{"size": 20, "color": "DarkSlateGrey"}})

    fig2 = px.scatter_map(
        FSR,
        lat = 'Lat',
        lon = 'Lon',
        color='FSR',
        hover_name='Territory Name',
        hover_data={'Lat': False,
                    'Lon': False,
                    'FSR': False,
                    'Territory Name': False},
        text = 'FSR',
        zoom=zoom_var,
        center={'lat': lat_center, 'lon': lon_center},
        size_max=20)
    fig2.update_traces(
        mode='markers+text',
        textposition='top center', 
        textfont_color="black", 
        marker={"size": 13, "symbol": ["star"], "allowoverlap": True}, 
        below='',
        showlegend = False)
    
    fig = fig1
    for trace in fig2.data:
        fig.add_trace(trace)
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, width=1300, height=700, clickmode='select')
    fig.update_layout(map_layers=[{
                          "name": "GeoJSON Layer", # Optional name for the layer
                          "below": 'traces',       # Place the GeoJSON below the scatter points
                          "sourcetype": "geojson",
                          "type": "line",          # Or "line" for outlines, "symbol" for markers
                          #"color": "#CCCCCC", 
                          "color": "#F6BCBA",        # Color of the GeoJSON features
                          "source": gj             # Your loaded GeoJSON data
                      }])

    return fig


def nearest_neighbor_tsp(distance_matrix):
    n = len(distance_matrix)
    visited = [False] * n
    route = [0]
    visited[0] = True

    for _ in range(n - 1):
        last_city = route[-1]
        nearest_city = min(
            [(i, distance_matrix[last_city][i]) for i in range(n) if not visited[i]],
            key=lambda x: x[1]
        )[0]
        route.append(nearest_city)
        visited[nearest_city] = True

    route.append(0)
    total_distance = sum(distance_matrix[route[i]][route[i+1]] for i in range(n))
    return total_distance

def clustering_by_country(df, terr_num):
    new_number = terr_num
    k_means = KMeans(init = "k-means++", n_clusters = new_number, max_iter=100, verbose=0, n_init=1, random_state=42)
    df['Cluster'] = k_means.fit_predict(df[['Lat', 'Lon']])
    df['Territory'] = df['Cluster'].astype(str)

    #brick_name_list = []
    #for i in range(df['Cluster'].nunique()):
    #    if brick_name_list == None:
    #        brick_name_list.append(df[df['Cluster'] == i].groupby(['Cluster', 'Territory']).agg({'Brick Name': 'count'}).sort_values(by=['Brick Name'], ascending=False).reset_index()['Territory'].values[0])
    #        df.loc[df['Cluster'] == i, 'Territory'] = df[df['Cluster'] == i].groupby(['Cluster', 'Territory']).agg({'Brick Name': 'count'}).sort_values(by=['Brick Name'], ascending=False).reset_index()['Territory'].values[0]
    #    else:
    #        if df[df['Cluster'] == i].groupby(['Cluster', 'Territory']).agg({'Brick Name': 'count'}).sort_values(by=['Brick Name'], ascending=False).reset_index()['Territory'].values[0] not in brick_name_list:
    #            brick_name_list.append(df[df['Cluster'] == i].groupby(['Cluster', 'Territory']).agg({'Brick Name': 'count'}).sort_values(by=['Brick Name'], ascending=False).reset_index()['Territory'].values[0])
    #            df.loc[df['Cluster'] == i, 'Territory'] = df[df['Cluster'] == i].groupby(['Cluster', 'Territory']).agg({'Brick Name': 'count'}).sort_values(by=['Brick Name'], ascending=False).reset_index()['Territory'].values[0]    
    #        else:
    #            if df[df['Cluster'] == i].groupby(['Cluster', 'Territory']).agg({'Brick Name': 'count'}).sort_values(by=['Brick Name'], ascending=False).reset_index()['Territory'].values[1] not in brick_name_list:
    #                brick_name_list.append(df[df['Cluster'] == i].groupby(['Cluster', 'Territory']).agg({'Brick Name': 'count'}).sort_values(by=['Brick Name'], ascending=False).reset_index()['Territory'].values[1])
    #                df.loc[df['Cluster'] == i, 'Territory'] = df[df['Cluster'] == i].groupby(['Cluster', 'Territory']).agg({'Brick Name': 'count'}).sort_values(by=['Brick Name'], ascending=False).reset_index()['Territory'].values[1]
    #            else:
    #                brick_name_list.append(df[df['Cluster'] == i].groupby(['Cluster', 'Territory']).agg({'Brick Name': 'count'}).sort_values(by=['Brick Name'], ascending=False).reset_index()['Territory'].values[2])
    #                df.loc[df['Cluster'] == i, 'Territory'] = df[df['Cluster'] == i].groupby(['Cluster', 'Territory']).agg({'Brick Name': 'count'}).sort_values(by=['Brick Name'], ascending=False).reset_index()['Territory'].values[2]

def clustering_by_fsr(df, FSR):
    centroids = FSR[['Lat', 'Lon']]
    labels = FSR['Territory Name']
    clf = NearestCentroid()
    clf.fit(centroids, labels)

    df['Territory'] = clf.predict(df[['Lat', 'Lon']])    


@st.cache_data
def load_data(uploaded_file):
    df = pd.read_excel(uploaded_file)
    return df


def get_brick(df, current_territory, event_value):
    if "bricks" not in st.session_state:
        st.session_state.bricks = []
    if "current_brick_list" not in st.session_state:
        st.session_state.current_brick_list = []
    
    st.session_state.bricks = list(df[df['Territory'] == current_territory]['Brick Name'].unique())
    st.session_state.bricks.sort()
    
    if event_value == None:
        bricks_list = st.sidebar.multiselect("Current Brick", st.session_state.bricks)
        return bricks_list
    else:
        st.session_state.event_value = event_value
        st.session_state.current_brick_list.append(event_value)
        st.session_state.bricks = set(st.session_state.current_brick_list)
        bricks_list = st.sidebar.multiselect('', list(st.session_state.bricks), list(st.session_state.bricks))
        return bricks_list


def update_selection():
    event = st.session_state.my_chart
    if len(event.selection.points) != 0:
        st.session_state.event_value = event["selection"]["points"][0]["customdata"][0]


@st.cache_data
def load_geojson():
    return json.load(open("./georef-germany-land.geojson", 'r'))


@st.cache_data
def simplify_geojson(tolerance=0.01):
    gdf = gpd.read_file("./georef-germany-kreis.geojson")
    gdf["geometry"] = gdf.simplify(tolerance, preserve_topology=True)
    return gdf.__geo_interface__




def main():
    #Page settings
    st.set_page_config(layout='wide')
    st.title(APP_TITLE)
    
    placeholder = st.empty()
    placeholder.header('Upload a file')
    placeholder.write('Upload an Excel file containing "Territory", "Brick Name", latitude and longitude data')
    uploaded_file = placeholder.file_uploader('Choose a file')
    if uploaded_file is None:
        st.info("⚠️ Upload a file through 'Browse files'")
        st.stop()
    else:
        placeholder.empty()
    if "df" not in st.session_state:
        st.session_state.df = load_data(uploaded_file)
    df = st.session_state.df


    if "plotly_uirevision" not in st.session_state:
        st.session_state.plotly_uirevision = 1
    if "geojson_data_kreis" not in st.session_state:
        st.session_state.geojson_data_kreis = simplify_geojson(tolerance=0.01)
    if "geojson_data_land" not in st.session_state:
        st.session_state.geojson_data_land = load_geojson()
    

    #Display filters
    ter_list = list(df['Territory'].unique())
    ter_list.sort()
    territory = st.multiselect('Territory', ter_list)
    

    #Display sidebar
    #Clustering
    st.sidebar.header("Update the number of SalesReps:")
    uploaded_fsr = st.sidebar.file_uploader('Choose a file with SalesRep list')
    if uploaded_fsr is None:
        st.sidebar.info("⚠️ Upload a file through 'Browse files'")
        st.stop()
    else:
        pass
    if "fsr" not in st.session_state:
        st.session_state.fsr = load_data(uploaded_fsr)
    else:
        st.session_state.fsr = load_data(uploaded_fsr)
    FSR = st.session_state.fsr
    
    
    terr_num = st.sidebar.number_input("Select Number of Future Territories", min_value=0, max_value=40, step=1, value=30)
        
    if st.sidebar.button("Redistribute Territories by country", type='primary'):
        clustering_by_country(df, terr_num)
    
    st.sidebar.divider() 
    if st.sidebar.button("Redistribute Territories by FSR", type='primary'):
        clustering_by_fsr(df, FSR)


    st.sidebar.divider()    
    
    #From
    st.sidebar.header("Manual reassignment")
    st.sidebar.subheader("Current:")
    current_territory = st.sidebar.selectbox("Current Territory", ter_list)
    if "event_value" not in st.session_state:
        st.session_state.event_value = None
    current_bricks = get_brick(df, current_territory, st.session_state.event_value)
    if current_bricks == []:
        st.session_state.event_value = None
        st.session_state.current_brick_list = []
    
    #Transfer
    st.sidebar.subheader("Transfer To:")
    new_territory = st.sidebar.selectbox("New Territory", ter_list)
    if st.sidebar.button("Transfer selected bricks", type='primary'):
        df.loc[df['Brick Name'].isin(current_bricks), 'Territory'] = new_territory
        st.session_state.event_value = None
        st.session_state.current_brick_list = []
    
    #Download
    FSR_download = FSR.rename(columns={'Territory Name': 'Territory'})
    df_download = df.merge(FSR_download [['Territory', 'FSR']], on='Territory', how='left').reset_index(drop = True)
    df_download['FSR'] = df_download['FSR'].fillna('')
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_download[['Territory', 'FSR', 'Brick_code', 'Brick Name', 'Lat', 'Lon', 'Tier1', 'Tier2', '# Accounts']].to_excel(writer, sheet_name='Sheet1', index=False)
    st.sidebar.download_button(label='📥 Download Current Result',
                                data=buffer,
                                file_name= 'New territories.xlsx',
                                mime='application/vnd.ms-excel')


    #Display ter_num and capacity
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current number of Territories", value=df['Territory'].nunique())
    with col2:
        st.metric("Average # Accounts", value = round(df['# Accounts'].sum()/df['Territory'].nunique()))
    

    #Display dataframe
    with st.expander("Data View"):
        df_dist = pd.DataFrame(columns=['Territory', 'Distance, km'])
        for terr in df['Territory'].unique():
            df_1 = df[df['Territory'] == terr][['Lat', 'Lon']]
            fsr_1 = FSR[FSR['Territory Name'] == terr][['Lat', 'Lon']]
            cities = pd.concat([fsr_1, df_1]).reset_index(drop = True)
            dist = DistanceMetric.get_metric('haversine')
            dist_matrix = (dist.pairwise(cities[['Lat', 'Lon']]))
            distance = round(nearest_neighbor_tsp(dist_matrix) * 111.300, 0)
            df_dist = pd.concat([df_dist, pd.Series({'Territory': terr, 'Distance, km': distance}).to_frame().T])

       
        df_filtered = df.groupby(['Territory']).agg({'Tier1': 'sum', 'Tier2': 'sum', '# Accounts': 'sum'}).astype(int).reset_index()
        df_filtered = df_filtered.merge(df_dist[['Territory', 'Distance, km']], on = 'Territory', how = 'left')
        df_filtered = df_filtered[['Territory', '# Accounts', 'Tier1', 'Tier2', 'Distance, km']]
        
        if territory == []:
            st.dataframe(df_filtered, use_container_width=True)
        else:
            st.dataframe(df_filtered[df_filtered['Territory'].isin(territory)], use_container_width=True)
        
    #Display map
    st.session_state.px_map = display_map(df, FSR, territory)
    event = st.plotly_chart(st.session_state.px_map,
                            use_container_width=True,
                            key="my_chart", 
                            selection_mode="points",
                            on_select=update_selection,
                            config = {'displayModeBar': False},
                            )

    st.dataframe(FSR, use_container_width=True)


if __name__ == "__main__":
    main()
