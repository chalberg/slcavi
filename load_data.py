# Purpose: Process data from National Weather Service (NWS) for use in ML prediction
# Data Sources
#   National Weather Service: https://www.weather.gov/wrh/climate?wfo=slc
#   Climate Data Online: https://www.ncdc.noaa.gov/cdo-web/datasets
#       - Alta station: https://www.ncei.noaa.gov/cdo-web/datasets/GHCND/stations/GHCND:USC00420072/detail
# TO DO
# 1) Load in CSV for one station (ALTA)
# 2) Cleaning function for single day single station
# 3) Load all winter days (Oct - Apr) in past 10 years
# 4) Create Pytorch dataset from data

import pandas as pd
import numpy as np
from datetime import date

__all__ = ['clean_uac_avalanche_data',
           'clean_noaa_daily_data']

def clean_uac_avalanche_data(df):
    # filter for salt lake regions only
    df = df.loc[df['Region'] == 'Salt Lake']
    
    # drop unnecessary columns
    df.drop(columns = ['Comments 1',
             'Comments 2',
             'Comments 3',
             'Comments 4',
             'Weather Conditions and History',
             'Terrain Summary',
             'Accident and Rescue Summary',
             'Trigger: additional info',
             'Region'], axis=1, inplace=True)
    
    df['Date'] = pd.to_datetime(df['Date'])

    # convert coordinates to float columns
    df[['Latitude', 'Longitude']] = df['Coordinates'].str.split(',', expand=True)
    df['Latitude'] = pd.to_numeric(df['Latitude'])
    df['Longitude'] = pd.to_numeric(df['Longitude'])
    df.drop('Coordinates', axis=1, inplace=True)

    # convert to numeric
    df['Avi_depth'] = pd.to_numeric(df['Depth'].str.replace('"', "").str.replace("'", "").str.strip())
    df['Avi_width'] = pd.to_numeric(df['Width'].str.replace('"', "").str.replace("'", "").str.replace(",", "").str.strip())
    df['Avi_vertical'] = pd.to_numeric(df['Vertical'].str.replace('"', "").str.replace("'", "").str.replace(",", "").str.strip())
    df['Elevation'] = pd.to_numeric(df['Elevation'].str.replace(',','').str.replace("'", "").str.strip())

    # one-hot encodings
    one_hot = lambda x: x.astype(int)
    #regions = pd.get_dummies(df['Region'].str.replace(" ", "").str.strip(), prefix='region').apply(one_hot)
    #places = pd.get_dummies(df['Place'].str.replace(" ", "").str.strip(), prefix='place').apply(one_hot)
    trigger = pd.get_dummies(df['Trigger'].str.replace(" ", "").str.strip(), prefix='trigger').apply(one_hot)
    aspect = pd.get_dummies(df['Aspect'], prefix='aspect').apply(one_hot)
    layer = pd.get_dummies(df["Weak Layer"].str.replace("/", "").str.strip(), prefix='layer').apply(one_hot)
    df = pd.concat([df, trigger, aspect, layer], axis=1)
    df.drop(['Trigger', 'Aspect', 'Weak Layer'], axis=1, inplace=True)
    
    return df

def clean_noaa_daily_data():
    df = pd.read_csv('data/noaa_wasatch_daily.csv')

    df = df.loc[df['SNWD'] != 0.0] # drop days with no snow depth

    # rename columns
    df.rename(columns={'NAME': 'Name',
                       'LATITUDE': 'Latitude',
                       'LONGITUDE': 'Longitude',
                       'ELEVATION': 'Elevation',
                       'DATE': 'Date',
                       'PRCP': 'Precip',
                       'SNOW': 'Snow',
                       'SNWD': 'Snow_depth',
                       'TMAX': 'Temp_max',
                       'TMIN': 'Temp_min',
                       'TOBS': 'Temp_OBS',
                       'WT01': 'Fog',
                       'WT03': 'Thunder',
                       'WT04': 'Sleet',
                       'WT05': 'Hail',
                       'WT06': 'Rime',
                       'WT11': 'High_winds'}, inplace=True)
    
    df['Date'] = [date.fromisoformat(d) for d in df['Date']] # convert str --> datetime

    # create "WNTR" variable to label winter season
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

#def combine_noaa_data():
#    stations_dict = get_stations_dict()
#    dfs = []
#    for df in stations_dict.values():
#        dfs.append(clean_noaa_daily_data(df))
#
#    return pd.concat(dfs, ignore_index=True)
#
#def get_stations_dict() -> dict:
#    # separate csv by site into dict of individual dataframes
#    df = pd.read_csv('data/noaa_wasatch_daily.csv')
#    stations_dict = {}
#    for name in df['NAME'].unique():
#        stations_dict[name] = df.loc[df['NAME'] == name]
#
#    return stations_dict