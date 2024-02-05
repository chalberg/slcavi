import folium
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from data_utils import *
from argparse import ArgumentParser

__all__ = ['get_avalanche_map']

__name__=="__main__"

def get_colormap():
    cmap_dict = {}
    cmap_dict["trigger"] = {
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
    
    cmap_dict["layer"] = {
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

    return cmap_dict

def get_avalanche_map():
    
    df = clean_uac_avalanche_data()

    # create scaled avi volumes where data exists
    mask = df.loc[df['Avi_volume']!="Unknown"].index.to_list()
    avi_vols = df.loc[mask, 'Avi_volume'].values.reshape(-1, 1)
    scaler = MinMaxScaler().fit(avi_vols)
    scaled_vols = scaler.transform(avi_vols)
    vols_dict = {idx: value[0] for idx, value in zip(mask, scaled_vols)}

    # initilize map
    map_lat = df['Latitude'][0]
    map_long = df['Longitude'][0]

    m = folium.Map([map_lat, map_long], zoom_start=12)
    
    # add topographical map option
    attr = 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community'
    esri_topo = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}'
    tile = folium.TileLayer(esri_topo, attr=attr, name="Topographical Map")
    tile.add_to(m)

    layer_group = folium.FeatureGroup(name="Weak Layer Markers")
    trigger_group = folium.FeatureGroup(name="Trigger Markers")

    cmap_dict = get_colormap()
    layer_cmap = cmap_dict['layer']
    trigger_cmap = cmap_dict['trigger']

    # create markers for each avalanche incident
    for idx, event in df.iterrows():

        # size scaled to volume of avalanche
        aspect_ratio = 0.78
        if event['Avi_volume'] != "Unknown":
            h = np.sqrt(vols_dict[idx] / aspect_ratio) * 20
            w = aspect_ratio * h
            if h >= 20: # min size; othewise some icons will barely be visible
                size = [w, h]
            else: 
                size = [aspect_ratio*20, 20]
        else:
            size = [aspect_ratio*20, 20]
        
        # create trigger marker
        color = str("map_marker_icon_") + str(trigger_cmap[event['Trigger']])
        popup = """
            Place: {}
            Date: {}
            Trigger: {}
            Terrain Summary: {}
            Additional info: {}
            """.format(event['Place'], event['Date'], event['Trigger'], event['Terrain_summary'], event['Trigger_info'])
        image = "static/assets/map_marker/{}.png".format(color)
        icon = folium.CustomIcon(image, icon_size=size)

        folium.Marker(
            location=[event['Latitude'], event['Longitude']],
            popup= popup,
            icon=icon
            ).add_to(trigger_group)
        
        # create layer marker
        color = str("map_marker_icon_") + str(layer_cmap[event['WeakLayer']])
        popup = """
                Place: {}
                Date: {}
                Weak Layer: {}
                Terrain Summary: {}
                Additional Info: {}
                """.format(event['Place'], event['Date'], event['WeakLayer'],event['Terrain_summary'], event['Trigger_info'])
        image = "static/assets/map_marker/{}.png".format(color)
        icon = folium.CustomIcon(image, icon_size=size)

        folium.Marker(
            location=[event['Latitude'], event['Longitude']],
            popup= popup,
            icon=icon
            ).add_to(layer_group)
        
    layer_group.add_to(m)
    trigger_group.add_to(m)
    folium.LayerControl().add_to(m)

    return m

def save_map_assets():
    uac_map = get_avalanche_map()
    uac_map.save('templates/avi_map.html')
    
if __name__=="__main__":
    parser = ArgumentParser()

    parser.add_argument('--save', action='store_true')

    args = parser.parse_args()

    if args.save:
        save_map_assets()

        print("Save successful.")
    else:
        print("Save not requested.")
    