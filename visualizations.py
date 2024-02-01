import folium
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from data_utils import *

__all__ = ['get_avalanche_map']

def get_colormap(marker_type):
    if marker_type not in {"trigger", "layer"}:
        raise ValueError("Color map must be either 'trigger' or 'layer'")
    
    if marker_type == "trigger":
        cmap = {
            'Explosive': 'black',
            'Hiker': 'yellow',
            'Natural': 'green',
            'Skier': 'red',
            'SnowBike': 'red',
            'Snowboarder': 'red',
            'Snowmobiler': 'orange',
            'Snowshoer': 'yellow',
            'Unknown': 'gray'
            }
    
    if marker_type == "layer":
        cmap = {
            'NewSnowOldSnowInterface':'yellow',
            'Facets':'red',
            'NewSnow':'white',
            'GroundInterface':'green',
            'SurfaceHoar':'lightpurple',
            'DepthHoar':'purple',
            'DensityChange':'orange',
            'Graupel':'lightblue',
            'Wetgrains':'blue',
            'Unknown':'gray'
            }

    return cmap

def get_avalanche_map(marker_type):
    if marker_type not in {'trigger', 'layer'}:
        raise ValueError("Marker type should be either 'trigger' or 'layer'")
    
    df = clean_uac_avalanche_data()

    # create scaled avi volumes where data exists
    mask = df.loc[df['Avi_volume']!="Unknown"].index.to_list()
    avi_vols = df.loc[mask, 'Avi_volume'].values.reshape(-1, 1)
    scaler = MinMaxScaler().fit(avi_vols)
    scaled_vols = scaler.transform(avi_vols)
    vols_dict = dict(zip(mask, scaled_vols))

    # initilize map
    map_lat = df['Latitude'][0]
    map_long = df['Longitude'][0]

    m = folium.Map([map_lat, map_long], zoom_start=12)

    # create markers for each avalanche incident
    for idx, event in df.iterrows():
        
        # color according to trigger or layer
        cmap = get_colormap(marker_type)
        if marker_type == "trigger":
            color = str("map_marker_icon_") + str(cmap[event['Trigger']])

        if marker_type == 'layer':
            color = str("map_marker_icon_") + str(cmap[event['Layer']])

        image = "assets/map_markers/{}.png".format(color)

        # size scaled to volume of avalanche
        aspect_ratio = 0.78
        if event['Avi_volume'] != "Unknown":
            h = np.sqrt(vols_dict[idx] / aspect_ratio)
            w = aspect_ratio * h
            size = [w, h]
        else:
            size = [aspect_ratio*0.5, 0.5]

        icon = folium.CustomIcon(image, icon_size=size)

        folium.Marker(
            location=[event['Latitude'], event['Longitude']],
            popup= event['Place'] + ", " + str(event['Date']),
            icon=icon
        ).add_to(m)

    return m