import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from datetime import datetime
from tqdm import tqdm
import time

__all__ = ['clean_avalanche_data',
           'clean_noaa_daily_data',
           'get_uac_forecast']

def clean_avalanche_data():
    df = pd.read_csv('data/avalanches.csv') # avalanches.csv

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
        'Terrain Summary': 'Terrain_summary',
        'Weak Layer': 'WeakLayer'}, inplace=True)
    
    df['Date'] = pd.to_datetime(df['Date']).dt.floor('D')

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
    trigger = pd.get_dummies(df['Trigger'], prefix='Trigger').apply(one_hot)
    aspect = pd.get_dummies(df['Aspect'], prefix='Aspect').apply(one_hot)
    layer = pd.get_dummies(df["WeakLayer"], prefix='Layer').apply(one_hot)
    df = pd.concat([df, trigger, aspect, layer], axis=1)

    # create avalanche volume approximation
    df['Avi_volume'] = df['Avi_depth'] * df['Avi_width'] * df['Avi_vertical']
    df['Avi_volume'] = df['Avi_volume'].fillna("Unknown")

    # fill NA
    df['Trigger_info'] = df['Trigger_info'].fillna('NA')
    df['Terrain_summary'] = df['Terrain_summary'].fillna('NA')

    df = avalanche_to_ts(df)
    return df

def clean_noaa_daily_data():
    df = pd.read_csv('data/noaa_wasatch_daily.csv')

    df = df.loc[df['SNWD'] != 0.0] # drop days with no snow depth
    df.drop(columns=['STATION'], inplace=True)

    # rename columns
    df.rename(columns={'NAME': 'Name',
                       'LATITUDE': 'latitude',
                       'LONGITUDE': 'longitude',
                       'ELEVATION': 'elevation',
                       'DATE': 'date',
                       'PRCP': 'precip',
                       'SNOW': 'snow',
                       'SNWD': 'snow_depth',
                       'TMAX': 'temp_max',
                       'TMIN': 'temp_min',
                       'TAVG': 'temp_avg',
                       'TOBS': 'temp_obs',
                       'WESD': 'water_equiv_groundsnow',
                       'WESF': 'water_equiv_snowfall',
                       'WT01': 'fog',
                       'WT03': 'thunder',
                       'WT04': 'sleet',
                       'WT05': 'hail',
                       'WT06': 'rime',
                       'WT11': 'high_winds'}, inplace=True)
    
    df['date'] = pd.to_datetime(df['date']) # convert str --> datetime

    # create "WNTR" variable to label winter season (Oct 1st - May 5th)
    wntrs = {
        '16_17': (pd.Timestamp(2016, 10, 1), pd.Timestamp(2017, 5, 30)),
        '17_18': (pd.Timestamp(2017, 10, 1), pd.Timestamp(2018, 5, 30)),
        '18_19': (pd.Timestamp(2018, 10, 1), pd.Timestamp(2019, 5, 30)),
        '19_20': (pd.Timestamp(2019, 10, 1), pd.Timestamp(2020, 5, 30)),
        '20_21': (pd.Timestamp(2020, 10, 1), pd.Timestamp(2021, 5, 30)),
        '21_22': (pd.Timestamp(2021, 10, 1), pd.Timestamp(2022, 5, 30)),
        '22_23': (pd.Timestamp(2022, 10, 1), pd.Timestamp(2023, 5, 30)),
        '23_24': (pd.Timestamp(2023, 10, 1), pd.Timestamp(2024, 5, 30))
    }

    df['winter'] = np.select(
        [((df['date'] >= start) & (df['date'] <= end)) for start, end in wntrs.values()],
        list(wntrs.keys()),
        default = "")
    
    station_names = {
        'ALTA, UT US': 'Alta',
        'COTTONWOOD HEIGHTS 1.6 SE, UT US': 'CottonwoodHeights',
        'SILVER LAKE BRIGHTON, UT US': 'SilverLakeBrighton',
       'SNOWBIRD, UT US': 'Snowbird',
       'BRIGHTON, UT US': 'Brighton'
    }
    df['Name'] = df['Name'].replace(station_names)

    return noaa_to_ts(df)

def clean_forecast_data():
    df = pd.read_csv('uac_forecasts.csv')
    df = df.dropna('any', axis=0)
    return df

def noaa_to_ts(df):
    df.set_index('date', inplace=True)
    df = df.pivot(columns='Name')
    df.columns = [f"{station}_{variable}" for (variable, station) in df.columns]
    df = df.reindex(sorted(df.columns), axis=1)

    weather_cols = ['Alta_rime', 'Alta_fog', 'Alta_hail', 'Alta_high_winds', 'Alta_sleet', 'Alta_thunder',
                    'Brighton_rime', 'Brighton_fog', 'Brighton_hail', 'Brighton_high_winds', 'Brighton_sleet', 'Brighton_thunder',
                    'CottonwoodHeights_rime', 'CottonwoodHeights_fog', 'CottonwoodHeights_hail', 'CottonwoodHeights_high_winds', 'CottonwoodHeights_sleet', 'CottonwoodHeights_thunder',
                    'SilverLakeBrighton_rime', 'SilverLakeBrighton_fog', 'SilverLakeBrighton_hail', 'SilverLakeBrighton_high_winds', 'SilverLakeBrighton_sleet', 'SilverLakeBrighton_thunder',
                    'Snowbird_rime', 'Snowbird_fog', 'Snowbird_hail', 'Snowbird_high_winds', 'Snowbird_sleet', 'Snowbird_thunder']

    static_cols = ['Alta_latitude', 'Alta_longitude', 'Alta_elevation',
                'Brighton_latitude', 'Brighton_longitude', 'Brighton_elevation',
                'CottonwoodHeights_latitude', 'CottonwoodHeights_longitude', 'CottonwoodHeights_elevation',
                'SilverLakeBrighton_latitude', 'SilverLakeBrighton_longitude', 'SilverLakeBrighton_elevation',
                'Snowbird_latitude', 'Snowbird_longitude', 'Snowbird_elevation']
    # handle NA values
    for col in df.columns:
        df[col].apply(pd.to_numeric, errors='coerce')
        if col in weather_cols:
            df[col] = df[col].fillna(0).astype(int)
        elif col in static_cols:
            df[col] = df[col].bfill().ffill()
        else:
            df[col] = df[col].fillna(np.nan)

    df.dropna(axis=1, how='all', inplace=True)
    return df

def avalanche_to_ts(df):
    # drop unneccesary cols
    df.drop(columns=['Place', 'Trigger', 'Trigger_info', 'WeakLayer',
                     'Caught', 'Carried', 'Buried_partly', 'Buried_fully',
                     'Injured', 'Killed', 'Terrain_summary', 'Depth', 'Width',
                     'Vertical', 'Aspect'],
            axis=1, inplace=True)
    df.set_index('Date', inplace=True)
    return df

def get_uac_forecast():

    aspect_px_dict = {
        'L_N': (200, 75),
        'L_NE': (285, 95),
        'L_E': (320, 175),
        'L_SE': (290, 250),
        'L_S': (200, 290),
        'L_SW': (110, 255),
        'L_W': (85, 175),
        'L_NW': (110, 100),
        'M_N': (200, 100),
        'M_NW': (150, 120),
        'M_W': (130, 170),
        'M_SW': (150, 220),
        'M_S': (200, 230),
        'M_SE': (250, 220),
        'M_E': (275, 170),
        'M_NE': (250, 120),
        'H_N': (200, 135),
        'H_NW': (175, 135),
        'H_W': (168, 155),
        'H_SW': (178, 178),
        'H_S': (200, 185),
        'H_SE': (225, 175),
        'H_E': (235, 155),
        'H_NE': (225, 135) 
    }

    rgb_danger_dict = {
        (80, 184, 72, 255): 1, # green
        (255, 242, 0, 255): 2, # yellow
        (247, 148, 30, 255): 3, # orange
        (237, 28, 36, 255): 4, # red
        (0, 0, 0, 255): 5, # black
        (192, 192, 192): 'NA' # grey
    }

    # scrape available dates from UAC page
    urls = []
    dates = []
    print("Preparing data sources ...")
    for i in tqdm(range(18)): # num pages hard-coded for now
        time.sleep(0.5)
        if i == 0:
            date_url = 'https://utahavalanchecenter.org/archives/forecasts/salt-lake'
        else:
            date_url = 'https://utahavalanchecenter.org/archives/forecasts/salt-lake?page='+str(i)
        
        response = requests.get(date_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        for td in soup.find_all('td', class_='views-field views-field-title'):
            a_tag = td.find('a')
            if a_tag:
                href = a_tag['href']
                date_str = href.split('salt-lake/')[1]
                url = 'https://utahavalanchecenter.org/forecast/salt-lake/'+str(date_str)
                urls.append(url)

                if '-' in date_str:
                    date_str = date_str.split('-')[0]

                dates.append(datetime.strptime(date_str, "%m/%d/%Y"))
    
    # initialize df
    df = pd.DataFrame(index = dates, columns = aspect_px_dict.keys())
    print("Fetching forecasts from 2018-present ...")
    for idx in tqdm(range(len(urls))):
        time.sleep(0.25) # 0.25 second delay
        response = requests.get(urls[idx], timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        image_tag = soup.find('img', class_='full-width compass-width sm-pb3')

        if image_tag and 'src' in image_tag.attrs:
            image_url = 'http://utahavalanchecenter.org'+str(image_tag['src'])
            image_response = requests.get(image_url, timeout=10)

            # open image w/o saving to disk
            with Image.open(BytesIO(image_response.content)) as img:
                for k in aspect_px_dict.keys():
                    # get rgb val, map to danger level
                    rgb = img.getpixel(aspect_px_dict[k])
                    danger = rgb_danger_dict.get(rgb)
                    df.at[dates[idx], k] = danger
        else:
            print("Image not found or URL not provided in 'src' attribute of the <img> tag.")
        
    df2 = uac_forecast_pre2018(aspect_px_dict)
    df = pd.concat([df, df2])
    
    df.to_csv('data/uac_forecasts.csv')
    print("Done!")

def uac_forecast_pre2018(px_dict):
    rgb_danger_dict = {
            (80, 184, 72): 1, # green
            (255, 242, 0): 2, # yellow
            (247, 148, 30): 3, # orange
            (237, 28, 36): 4, # red
            (0, 0, 0): 5, # black
            (192, 192, 192): 'NA' # grey
        }

    base_url = 'https://utahavalanchecenter.org/archive/advisories/salt-lake'
    response = requests.get(base_url, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    d = soup.find('div', class_='text_02 body')

    urls  = []
    dates = []
    for a in d.find_all('a'):
        if int(a.text) > 20160801: # dates after 08/01/2016
            url = 'https://utahavalanchecenter.org'+str(a['href'])
            urls.append(url)
            dates.append(datetime.strptime(a.text, "%Y%m%d"))

    df = pd.DataFrame(index=dates, columns=px_dict.keys())

    print("Fetching forecasts from 2016-2018 ...")
    for idx in tqdm(range(len(urls))):
        #time.sleep(0.25) # 0.25 second delay
        response = requests.get(urls[idx], timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        d = soup.find('div', id='problem-rose')
        if d is not None:
            img_tag = d.find_all('img')[1]
            img_url = img_tag['src'].split('forecast/')[1]
            img_url = 'https://utahavalanchecenter.org/sites/default/files/archive/advisory/print/sites/default/files/forecast/'+str(img_url)
            img_response = requests.get(img_url, timeout=10)

            # open w/o saving to disk
            with Image.open(BytesIO(img_response.content)) as img:
                for k in px_dict.keys():
                    rgb = img.getpixel(px_dict[k])
                    danger = rgb_danger_dict.get(rgb)
                    df.at[dates[idx], k] = danger
    
    return df
