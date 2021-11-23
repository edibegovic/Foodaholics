
import pandas as pd
import urllib.parse

df = pd.read_json('result.json')

df.groupby('rguru_name').count()

df[:30]

locs = pd.read_csv('../data/places_combined_enriched.csv')[:10]

locs['name']

for idx, row in locs.iterrows():
    lat, lon = row['location'][1:-1].split(', ')
    name = urllib.parse.quote(row['name'])
    url = f'https://restaurantguru.com/search/{name}?sorting=distance&location=-1&geo_point={lat},{lon}'
    print(url)
