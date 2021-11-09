
import requests
import json
import pandas as pd

api_key = "AIzaSyB8xt1v6cCoeP7WBYnzb1MzndU9GGxCPw0"
base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?"

def get_parsed_response(url):
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    parsed = json.loads(response.text)
    return parsed

# ---------------------------------------------------------------
# Calculation windows

lon_500m = 0.008/2
lat_500m = 0.0045/2

lon_min, lon_max = 12.43943947366, 12.68002470150
lat_min, lat_max = 55.60302908406, 55.76820299353

lons = [lon_min+lon_500m*s for s in range(int((lon_max-lon_min)//lon_500m))]
lats = [lat_min+lat_500m*s for s in range(int((lat_max-lat_min)//lat_500m))]

# ---------------------------------------------------------------
# Scraping

places = {}

for lon in lons:
    for lat in lats:
        loc_string = f"{lat}%2C{lon}"
        url = f"{base_url}location={loc_string}&radius=300&type=restaurant&key={api_key}"
        response = get_parsed_response(url)

        results = response['results']

        if 'next_page_token' in response:
            next_page_token = response['next_page_token']
        else:
            next_page_token = None

        new_places = 0

        # First page
        for r in results:
            if r['place_id'] not in places:
                places[r['place_id']] = r
                new_places += 1

        # Check (up to 10) pages
        for pages in range(10):
            print(new_places)
            if new_places > 1 and next_page_token is not None:
                url = f"{base_url}pagetoken={next_page_token}&key={api_key}"
                response = get_parsed_response(url)

                results = response['results']

                if 'next_page_token' in response:
                    next_page_token = response['next_page_token']
                else:
                    next_page_token = None

                new_places = 0

                # First page
                for r in results:
                    if r['place_id'] not in places:
                        places[r['place_id']] = r
                        new_places += 1
            else:
                break


# ---------------------------------------------------------------
# Messy experimentation - ignore :)

len(places)

# Serialize data into file:
json.dump(places, open("places.json", 'w'))

import pickle
def save_obj(obj, name ):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

save_obj(places, "places")

places_formatted = {}

for key, r in places.items():
    if 'rating' in r:
        rating = r['rating']
    else:
        rating = None

    if 'user_ratings_total' in r:
        ratings_total = int(r['user_ratings_total'])
    else:
        ratings_total = None

    places_formatted[key] = {
            'name': r['name'],
            'address': r['vicinity'],
            'location': (r['geometry']['location']['lat'], r['geometry']['location']['lng']),
            'rating': rating,
            'total_ratings': ratings_total,
            'types': r['types'],
            'ref': r['reference']
            }

for p in places_formatted.values():
    if 'nemo' in p['name'].lower():
        print(p['name'])

len(places_formatted)

df = pd.DataFrame.from_dict(places_formatted, orient='index')

df.to_excel("places_limited.xlsx")
df.to_csv("places_limited.csv")
