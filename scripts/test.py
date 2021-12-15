
import pandas as pd

df = pd.read_csv('data/places_combined_enriched.csv')

df[df['smileys'].isnull()][['name', 'address']][200:250]

df['total_ratings'][200:250]

# Reviews
# ----------------------------------------------------

reviews = pd.read_csv('data/reviews.csv')

total_reviews = len(reviews.groupby('id').count())

df[df['total_ratings'].isnull() == False]

total_reviews-len(reviews[reviews['text'].isnull()])


from collections import Counter

df = # ---> name of the dataframe <---

s = ""
for i, r in df.iterrows():
    s += " " + (str(r['name']).rstrip()) + " "

counts = Counter(s.split())
sorted(counts, key=lambda i: i[1])
counts.most_common()[:30]
