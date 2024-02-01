import pandas as pd
import numpy as np
import matplotlib.colors as mcolors
import folium
from datetime import date

__all__ = ['clean_uac_avalanche_data',
           'clean_noaa_daily_data']

def clean_uac_avalanche_data():
    df = pd.read_csv('data/avalanches.csv')

    df = df.loc[df['Region'] == 'Salt Lake'] # filter for salt lake regions only

    # Remove spaces from strings and fill na with "Unknown"
    df[['Weak Layer', 'Trigger', 'Aspect']] = df[['Weak Layer', 'Trigger', 'Aspect']].fillna(value='Unknown')
    str_cols = ['Weak Layer', 'Trigger', 'Aspect', 'Region', 'Depth', 'Width', 'Vertical', 'Elevation']
    for col in str_cols:
        df[col] = df[col].str.replace(" ","").str.replace("/","").str.replace('"',"").str.replace(",","").str.replace("'","")

    # drop unnecessary columns
    df.drop(columns = [
        'Comments 1',
        'Comments 2',
        'Comments 3',
        'Comments 4',
        'Weather Conditions and History',
        'Accident and Rescue Summary',
        'Region'], axis=1, inplace=True)
    
    df.rename(columns={
        'Buried - Partly':'Buried_partly',
        'Buried - Fully':'Buried_fully',
        'Trigger: additional info': 'Trigger_info',
        'Terrain Summary': 'Terrain_summary'}, inplace=True)
    
    df['Date'] = pd.to_datetime(df['Date']).dt.floor('H')

    # convert coordinates to float columns
    df[['Latitude', 'Longitude']] = df['Coordinates'].str.split(',', expand=True)
    df['Latitude'] = pd.to_numeric(df['Latitude'])
    df['Longitude'] = pd.to_numeric(df['Longitude'])
    df.drop('Coordinates', axis=1, inplace=True)
    df = df.dropna(subset=['Latitude', 'Longitude'], axis=0) # drop events that don't have a lat, long location


    # convert to numeric
    df['Avi_depth'] = pd.to_numeric(df['Depth'])
    df['Avi_width'] = pd.to_numeric(df['Width'])
    df['Avi_vertical'] = pd.to_numeric(df['Vertical'])
    df['Elevation'] = pd.to_numeric(df['Elevation'])

    # one-hot encodings
    one_hot = lambda x: x.astype(int)
    #regions = pd.get_dummies(df['Region'], prefix='region').apply(one_hot)
    #places = pd.get_dummies(df['Place'], prefix='place').apply(one_hot)
    trigger = pd.get_dummies(df['Trigger'], prefix='Trigger').apply(one_hot)
    aspect = pd.get_dummies(df['Aspect'], prefix='Aspect').apply(one_hot)
    layer = pd.get_dummies(df["Weak Layer"], prefix='Layer').apply(one_hot)
    df = pd.concat([df, trigger, aspect, layer], axis=1)

    # create avalanche volume approximation
    df['Avi_volume'] = df['Avi_depth'] * df['Avi_width'] * df['Avi_vertical']
    df['Avi_volume'] = df['Avi_volume'].fillna("Unknown")

    # fill NA
    df['Trigger_info'] = df['Trigger_info'].fillna('NA')
    df['Terrain_summary'] = df['Terrain_summary'].fillna('NA')
    
    return df

def clean_noaa_daily_data():
    df = pd.read_csv('data/noaa_wasatch_daily.csv')

    df = df.loc[df['SNWD'] != 0.0] # drop days with no snow depth

    # rename columns
    df.rename(columns={'NAME': 'Name',
                       'STATION': 'Station',
                       'LATITUDE': 'Latitude',
                       'LONGITUDE': 'Longitude',
                       'ELEVATION': 'Elevation',
                       'DATE': 'Date',
                       'PRCP': 'Precip',
                       'SNOW': 'Snow',
                       'SNWD': 'Snow_depth',
                       'TMAX': 'Temp_max',
                       'TMIN': 'Temp_min',
                       'TAVG': 'Temp_avg',
                       'TOBS': 'Temp_OBS',
                       'WESD': 'Water_equiv_GroundSnow',
                       'WESF': 'Water_equiv_snowfall',
                       'WT01': 'Fog',
                       'WT03': 'Thunder',
                       'WT04': 'Sleet',
                       'WT05': 'Hail',
                       'WT06': 'Rime',
                       'WT11': 'High_winds'}, inplace=True)
    
    df['Date'] = [date.fromisoformat(d) for d in df['Date']] # convert str --> datetime

    # create "WNTR" variable to label winter season (Oct 1st - May 5th)
    wntrs = {
        '16_17': (date(2016, 10, 1), date(2017, 5, 30)),
        '17_18': (date(2017, 10, 1), date(2018, 5, 30)),
        '18_19': (date(2018, 10, 1), date(2019, 5, 30)),
        '19_20': (date(2019, 10, 1), date(2020, 5, 30)),
        '20_21': (date(2020, 10, 1), date(2021, 5, 30)),
        '21_22': (date(2021, 10, 1), date(2022, 5, 30)),
        '22_23': (date(2022, 10, 1), date(2023, 5, 30)),
        '23_24': (date(2023, 10, 1), date(2024, 5, 30))
    }

    df['WNTR'] = np.select(
        [((df['Date'] >= start) & (df['Date'] <= end)) for start, end in wntrs.values()],
        list(wntrs.keys()),
        default = "")

    return df

def noaa_to_ts(df):
    # returns dict of dfs coresponding to each station

    df_dict = {}
    for station in df['Name'].unique():
        station_df = df.loc[df['Station'] == station]
        station_df = station_df.sort_values(by='Date')
        station_df.set_index('Date')
        df_dict[station] = station_df

    return df_dict

def uac_to_ts(df):
    # returns dict of dfs corresponding to each station
    df.drop(['Trigger', 'Aspect', 'Weak Layer'], axis=1, inplace=True)