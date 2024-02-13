import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from datetime import datetime
from datetime import date
from tqdm import tqdm
import time

__all__ = ['clean_uac_avalanche_data',
           'clean_noaa_daily_data',
           'uac_to_ts',
           'get_uac_forecast']

def clean_uac_avalanche_data(data):
    df = data # avalanches.csv

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
    #regions = pd.get_dummies(df['Region'], prefix='region').apply(one_hot)
    #places = pd.get_dummies(df['Place'], prefix='place').apply(one_hot)
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

    # create column duplicates for each station, single dataframe with common date index
    df_dict = {}
    for station in df['Name'].unique():
        station_df = df.loc[df['Station'] == station]
        station_df = station_df.sort_values(by='Date')
        station_df.set_index('Date')
        df_dict[station] = station_df

    return df_dict

def uac_to_ts(df):
    
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
        (80, 184, 72, 255): 1,
        (255, 242, 0, 255): 2,
        (247, 148, 30, 255): 3,
        (237, 28, 36, 255): 4,
        (0, 0, 0, 255): 5
    }

    # scrape available dates from UAC page
    urls = []
    dates = []
    for i in range(18): # num pages hard-coded for now
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

                # clean and save dates
                if '-' in date_str:
                    date_str = date_str.split('-')[0]

                dates.append(datetime.strptime(date_str, "%m/%d/%Y"))
    
    # initialize df
    df = pd.DataFrame(index = dates, columns = aspect_px_dict.keys())
    for idx, url in tqdm(enumerate(urls)):
        time.sleep(0.25) # 0.25 second delay
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        image_tag = soup.find('img', class_='full-width compass-width sm-pb3')

        if image_tag and 'src' in image_tag.attrs:
            image_url = 'http://utahavalanchecenter.org'+str(image_tag['src'])
            image_response = requests.get(image_url)

            # open image w/o saving to disk
            with Image.open(BytesIO(image_response.content)) as img:
                for k in aspect_px_dict.keys():
                   # get rgb val, map to danger level
                   rgb = img.getpixel(aspect_px_dict[k])
                   danger = rgb_danger_dict.get(rgb)
                   df.at[dates[idx], k] = danger
        else:
            print("Image not found or URL not provided in 'src' attribute of the <img> tag.")
        
        if (idx % 50) == 0 and idx != 0:
            print("Saving data ...")
            df.to_csv('data/uac_forecasts.csv')
    
    print("Saving data ...")
    print("Done!")
    df.to_csv('data/uac_forecasts.csv')
    return df
