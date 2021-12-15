import pandas as pd
import ast
import geopandas as gpd
from shapely.geometry import Point

# read restaurant-dataset and geojson file which contains all city names of Denmark and their postal codes
df = pd.read_csv('data/places_combined.csv')
df_areas = gpd.read_file('data/postnumre.geojson')

# parse the coordinates-string and switch longitude and latitude position in tuple
df['location'] = df['location'].apply(lambda x: (ast.literal_eval(x)[1], ast.literal_eval(x)[0]))
df['latitude'] = df['location'].apply(lambda x: x[1])
df['longitude'] = df['location'].apply(lambda x: x[0])

# add columns
df['postal_code'] = ""
df['city_name'] = ""

# for each restaurant, check if its coordinates lies within the area of one of the specified cities in the .geojson file
for idx, row in df.iterrows():
    c = row.location
    for idx_y, y in df_areas.iterrows():
        if y.geometry.contains(Point(c)):
            # if it does, add postal code and city name to its entry in the dataset
            df.loc[idx, 'postal_code'] = y.POSTNR_TXT
            df.loc[idx, 'city_name'] = y.POSTBYNAVN

# save as new csv file
df.to_csv('data/places_combined_enriched.csv')
