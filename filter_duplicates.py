
import pandas as pd
import urllib.parse

# -------------------------------------------------------------

adf = pd.read_csv('data/places_combined_enriched2.csv')

columns_to_drop = ['Unnamed: 0', 'Unnamed: 0.1', 'Unnamed: 0.1.1', 'Unnamed: 0.1.1.1',
       'Unnamed: 0.1.1.1.1']
adf = adf.drop(columns_to_drop, axis=1)

# Removing locations with fewer than 2 reviews
# -------------------------------------------------------------

adf = adf[adf['total_ratings'].notnull()]
adf = adf[adf['total_ratings'] > 2]
adf = adf.reset_index()

# Finding duplicates
# -------------------------------------------------------------
same = adf.groupby('address').filter(lambda x:len(x) > 1)

places = [('Tasty Take Away', 'Tasty Take Away'),
    ('Pizza & Kebab World', 'Pizza & Kebab World R√∏dovr'),
    ('Damhus Grill & Kebab', 'Damhus Grill & Kebab'),
    ('Restaurant Bj√¶lkehuset', 'Bj√¶lkehuset'),
     ('Zula', 'Zula'),
     ('Atn Albasha', 'Albasha'),
     ('Restaurant Safari', 'Safari'),
     ('Sovs Takeaway', 'Sovs Takeaway'),
     ('The Audo', 'Kampot The Audo')]

# manually filter these with Excel
adf.to_csv('temp.csv')

# Casting and filling missing values
# -------------------------------------------------------------

temp = pd.read_excel('~/Desktop/Book8.xlsx')

temp['cvr_number'] = temp[['cvr_number']].fillna(value=0)
temp['cvr_number'] = temp['cvr_number'].astype(int)

temp['postal_code'] = temp['postal_code'].astype(str)

temp['rating'] = temp['rating'].astype(float)
temp['total_ratings'] = temp['total_ratings'].astype(int)

temp.to_csv('places_combined_enriched_filtered.csv')

