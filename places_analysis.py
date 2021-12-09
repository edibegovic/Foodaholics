import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
from scipy.stats import gaussian_kde
import ast
from sklearn.preprocessing import MinMaxScaler

pd.set_option('display.max_columns', None)

df = pd.read_csv('data/places_combined_enriched_filtered.csv')
df_areas = gpd.read_file('data/postnumre.geojson')


def data_transformation():
    df.drop(columns=['Unnamed: 0', 'types', 'business_status', 'website', 'opening_hours', 'formatted_phone_number',
                     'cvr_number', 'checked_findsmiley'], axis=1, inplace=True)
    df['location'] = df['location'].apply(lambda x: ast.literal_eval(x))

    df['smileys'] = df['smileys'].apply(lambda x: ast.literal_eval(x) if not pd.isnull(x) else np.nan)
    df['smileys_count'] = df['smileys'].apply(lambda x: 0 if isinstance(x, float) else (4 if 'Elite' in x else len(x)))
    df['smileys_average'] = df.apply(
        lambda x: np.nan if x.smileys_count == 0 else (1 if 'Elite' in x.smileys else sum(x.smileys) / x.smileys_count),
        axis=1)

    df['no_price'] = df['price_level'].apply(lambda x: 1 if pd.isnull(x) else 0)
    df['no_smileys'] = df['smileys_average'].apply(lambda x: 1 if pd.isnull(x) else 0)

    # traverse scores of price level and smiley average so 1 is the worst and 4 the best
    df['price_level_traversed'] = df['price_level'].max() - (df['price_level'] - df['price_level'].min())
    df['smileys_average_traversed'] = df['smileys_average'].max() - (
            df['smileys_average'] - df['smileys_average'].min())

    # handling missing price and smiley data by filling it with mean value
    df['price_level_traversed'].fillna(df['price_level_traversed'].mean(), inplace=True)
    df['smileys_average_traversed'].fillna(df['smileys_average_traversed'].mean(), inplace=True)

    # log transformation of total ratings
    df['total_ratings_log'] = df['total_ratings'].apply(np.log)

    # weight rating and price with log of total ratings
    df['rating_weighted'] = df['rating'] * df['total_ratings_log']
    df['price_weighted'] = df['price_level_traversed'] * df['total_ratings_log']

    scaler = MinMaxScaler()
    df['rating_scaled'] = scaler.fit_transform(df['rating'].values.reshape(-1, 1))
    df['price_scaled'] = scaler.fit_transform(df['price_level_traversed'].values.reshape(-1, 1))
    df['smileys_scaled'] = scaler.fit_transform(df['smileys_average_traversed'].values.reshape(-1, 1))

    df['ranking_scaled'] = df[['rating_scaled', 'price_scaled', 'smileys_scaled']].mean(axis=1)

    df['rating_weighted_scaled'] = scaler.fit_transform(df['rating_weighted'].values.reshape(-1, 1))
    df['price_weighted_scaled'] = scaler.fit_transform(df['price_weighted'].values.reshape(-1, 1))

    df['ranking_weighted_scaled'] = df[['rating_weighted_scaled', 'price_weighted_scaled', 'smileys_scaled']].mean(
        axis=1)

    coords = list(df.location)
    for index, x in df_areas.iterrows():
        polygon = x.geometry
        if not any(polygon.contains(Point(c)) for c in coords):
            df_areas.drop(index, inplace=True)


def general_statistics():
    print('GENERAL STATISTICS')
    print('__________________')
    print(df.describe(), '\n')


def top_performers():
    print('TOP PERFORMERS')
    print('__________________')

    cols = ['ranking_scaled', 'ranking_weighted_scaled']
    text = ['Ranking scaled', 'Ranking weighted and scaled']
    for i in range(len(cols)):
        print('TOP PERFORMERS - ' + text[i])
        print('__________________')
        print(df.sort_values(cols[i], ascending=False).head(5))


def map_distribution():
    fig = plt.figure(figsize=(10, 10))
    subplot_positions = [121, 122]

    ax = fig.add_subplot(subplot_positions[0])
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    df_areas.plot(ax=ax, color="lightgrey", edgecolor="darkgrey")
    df.plot(ax=ax, x="longitude", y="latitude", kind="scatter", color='moccasin', alpha=0.5, marker='o', s=20)

    # Generate fake data
    x = df['longitude']
    y = df['latitude']

    # Calculate the point density
    xy = np.vstack([x, y])
    z = gaussian_kde(xy)(xy)

    # Sort the points by density, so that the densest points are plotted last
    idx = z.argsort()
    x, y, z = x[idx], y[idx], z[idx]

    ax2 = fig.add_subplot(subplot_positions[1])
    ax2.spines['right'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax2.tick_params(labelleft=False, left=False)
    df_areas.plot(ax=ax2, color="lightgrey", edgecolor="darkgrey")
    ax2.scatter(x, y, c=z, s=20, marker='o', cmap='magma_r', alpha=0.5)


def map_cities():
    df_cities = df.groupby('city_name').agg({'ref': 'count',
                                             'total_ratings': 'mean',
                                             'total_ratings_log': 'mean',
                                             'rating': 'mean',
                                             'rating_scaled': 'mean',
                                             'price_level': 'mean',
                                             'price_scaled': 'mean',
                                             'no_price': 'sum',
                                             'smileys_average': 'mean',
                                             'smileys_scaled': 'mean',
                                             'no_smileys': 'sum',
                                             'rating_weighted_scaled': 'mean',
                                             'price_weighted_scaled': 'mean',
                                             'ranking_scaled': 'mean',
                                             'ranking_weighted_scaled': 'mean'}).reset_index()

    df_cities = df_cities.rename(columns={'city_name': 'POSTBYNAVN'})
    df_areas_cities = df_areas.merge(df_cities, how='left', on='POSTBYNAVN')

    fig = plt.figure(figsize=(15, 15))
    ax = fig.add_subplot(111)
    ax.set_axis_off()
    ax.set_title('Total Rating', fontsize=32)
    df_areas_cities.plot(column='total_ratings', cmap='magma_r', ax=ax, edgecolor='black',
                         missing_kwds={'color': 'lightgray', 'alpha': 0.3, 'hatch': '///', 'edgecolor': 'black',
                                       'linewidth': 0.2}, linewidth=0.2, label='Total Rating')
    plt.savefig('data/cities_map_total_ratings.png')

    fig = plt.figure(figsize=(15, 15))
    subplot_positions = [141, 142, 143, 144]
    columns = ['rating_scaled', 'price_scaled', 'smileys_scaled', 'ranking_scaled']
    titles = ['Rating', 'Price Level', 'Smileys', 'Ranking']
    for i in range(len(columns)):
        ax = fig.add_subplot(subplot_positions[i])
        ax.set_axis_off()
        ax.set_title(titles[i], fontsize=22)
        df_areas_cities.plot(column=columns[i], cmap='magma_r', ax=ax, edgecolor='black',
                             missing_kwds={'color': 'lightgray', 'alpha': 0.3, 'hatch': '///', 'edgecolor': 'black',
                                           'linewidth': 0.2}, linewidth=0.2, label=titles[i])
    plt.savefig('data/cities_map_original.png')

    fig = plt.figure(figsize=(15, 15))
    subplot_positions = [141, 142, 143, 144]
    columns = ['rating_weighted_scaled', 'price_weighted_scaled', 'smileys_scaled', 'ranking_weighted_scaled']
    titles = ['Rating Weighted', 'Price Weighted', 'Smileys', 'Ranking Weighted']
    for i in range(len(columns)):
        ax = fig.add_subplot(subplot_positions[i])
        ax.set_axis_off()
        ax.set_title(titles[i], fontsize=22)
        df_areas_cities.plot(column=columns[i], cmap='magma_r', ax=ax, edgecolor='black',
                             missing_kwds={'color': 'lightgray', 'alpha': 0.3, 'hatch': '///', 'edgecolor': 'black',
                                           'linewidth': 0.2}, linewidth=0.2, label=titles[i])
    plt.savefig('data/cities_map_weighted.png')


data_transformation()
general_statistics()
top_performers()
map_distribution()
map_cities()
