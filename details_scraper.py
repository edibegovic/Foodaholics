
import requests
import json
import pandas as pd

api_key = "AIzaSyAyS1OlKxVFjb8DxfYQ5svGgmkZgmYyHGs"
base_url = "https://maps.googleapis.com/maps/api/place/details/json?"

def get_parsed_response(url):
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    parsed = json.loads(response.text)
    return parsed

url = f"{base_url}place_id=ChIJH-sEy2hTUkYRU_3IhTF5sMM&key={api_key}"
response = get_parsed_response(url)

# ---------------------------------------------------------------
# Scraping

places = pd.read_csv('data/places_limited.csv')

places_details = {}

c = 1
for place in places['ref']:
    url = f"{base_url}place_id={place}&key={api_key}"
    response = get_parsed_response(url)
    if 'result' in response:
        result = response['result']
        if 'place_id' in result:
            places_details[result['place_id']] = result
    
    print(c)
    c += 1
    
import pickle
a_file = open("details_raw.pkl", "wb")
pickle.dump(places_details, a_file)

len(places_details)-len(places)

missing = set(places['ref'])-set(places_details.keys())
places.set_index('ref')

places_formatted = {}
# reviews = []
for key, r in places_details.items():
    bs = None
    fa = None
    fpn = None
    pl = None
    ws = None
    oh = None

    if (n := 'business_status') in r:
        bs = r[n]
    if (n := 'formatted_address') in r:
        fa = r[n]
    if (n := 'formatted_phone_number') in r:
        fpn = r[n]
    if (n := 'price_level') in r:
        pl = r[n]
    if (n := 'website') in r:
        ws = r[n]
    if (n := 'opening_hours') in r:
        oh = get_opening_hours(r[n])


    places_formatted[key] = {
            'business_status': bs,
            'formatted_address': fa,
            'formatted_phone_number': fpn,
            'price_level': pl,
            'website': ws,
            'opening_hours': oh,
            'ref': r['reference'],
            }

    # --------- REVIEWS ---------
    # if (n := 'reviews') in r:
    #     for review in r[n]:

    #         if (l := 'language') in review:
    #             l = review['language']
    #         else:
    #             l = None

            # reviews.append({
            #         'id': key,
            #         'author_name': review['author_name'],
            #         'language': l,
            #         'rating': review['rating'],
            #         'time': review['time'],
            #         'text': review['text']
            #         })


def get_opening_hours(v):
    times = []
    periods = v['periods']
    if len(periods) == 7:
        for d in periods:
            t = (d['open']['time'], d['close']['time'])
            times.append(t)
        # times = '; '.join(str(e) for e in times)
        return times
    return None


review_df = pd.DataFrame(reviews)
review_df.to_csv("data/reviews.csv")

details_df = pd.DataFrame.from_dict(places_formatted, orient='index')
details_df.to_csv("data/places_details.csv")

merged = places.merge(details_df, on="ref", how="left")
merged.to_csv("data/places_combined.csv")

for row in merged.iterrows():
    row = row[1]
    if row['formatted_address'] != row['address']:
        print(row['formatted_address'])
        print(row['address'])
        print()
