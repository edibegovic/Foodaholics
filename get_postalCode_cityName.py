import pandas as pd
import regex as re
import numpy as np
import json
import urllib
import requests


# parse postal code from 'formatted_address' by looking for 4-digit numbers
# between 1000 and 3210 (minimal and maximal postal code in our data set)
def get_postal_code(x):
    match = re.search('(?<=( )|^)[1-2][0-9]{3}|3[0-1][0-9]{2}|320[0-9]|3210(?= )', x)
    try:
        pc = int(match.group(0))
        return pc if 1000 <= pc <= 3210 else np.nan
    except:
        return np.nan


# return matching city name to given postal code
def get_city_name(x):
    for city, pc in postal_codes.items():
        if x in pc:
            return city


df = pd.read_csv('data/places_combined.csv')
# save postal code in new column
df['postal_code'] = df['formatted_address'].apply(lambda x: get_postal_code(x) if not pd.isnull(x) else np.nan)

# send request to zip code API
# https://www.back4app.com/database/taztest/denmark-zip-codes/get-started/python/rest-api/requests
where = urllib.parse.quote_plus("""
{
    "postalCode": {
        "$lte": "3210"
    }
}
""")
url = 'https://parseapi.back4app.com/classes/DK?limit=100000&order=postalCode&keys=place,postalCode&where=%s' % where
headers = {
    'X-Parse-Application-Id': 'dKJR8vtIeX3iDqINvh2vhqsl858s1ime7vAjL9Wo',  # This is the fake app's application id
    'X-Parse-Master-Key': '3Hfxuk9DofKGf75Z4tVCqfuYRhHnzmC1lJUFLUuu'  # This is the fake app's readonly master key
}
data = json.loads(requests.get(url, headers=headers).content.decode('utf-8'))  # Here you have the data that you need

# retrieve all postal codes for each city name from the API response
postal_codes = {}
for ele in data.get('results'):
    city = ele.get('place')
    pc = int(ele.get('postalCode'))
    if city not in postal_codes:
        postal_codes[city] = [pc]
    else:
        if pc not in postal_codes[city]:
            postal_codes[ele.get('place')].append(int(ele.get('postalCode')))

# save city name in new column
df['city_name'] = df['postal_code'].apply(lambda x: get_city_name(x))


df.to_csv('data/places_combined_enriched.csv')