import pandas as pd
import regex as re
import numpy as np
import json
import urllib
import requests
import ast
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt

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

    # handle missing values by replacing them with the mean value of the column
    df['price_level_filled'] = df['price_level']
    df['smileys_average_filled'] = df['smileys_average']
    df['price_level_filled'].fillna(df['price_level'].mean(), inplace=True)
    df['smileys_average_filled'].fillna(df['smileys_average'].mean(), inplace=True)

    # count missing values
    df['no_price'] = df['price_level'].apply(lambda x: 1 if pd.isnull(x) else 0)
    df['no_smileys'] = df['smileys_average'].apply(lambda x: 1 if pd.isnull(x) else 0)

    # traverse scores of price level and smiley average so 1 is the worst and 4 the best
    df['price_level_traversed'] = df['price_level'].max() - (df['price_level'] - df['price_level'].min())
    df['price_level_traversed_filled'] = df['price_level_traversed']
    df['price_level_traversed_filled'].fillna(df['price_level_traversed'].mean(), inplace=True)
    df['smileys_average_traversed'] = df['smileys_average'].max() - (
                df['smileys_average'] - df['smileys_average'].min())
    df['smileys_average_traversed_filled'] = df['smileys_average_traversed']
    df['smileys_average_traversed_filled'].fillna(df['smileys_average_traversed'].mean(), inplace=True)

    # log transformation of total ratings
    df['total_ratings_log'] = df['total_ratings'].apply(np.log)

    # weight rating and price with log of total ratings
    df['rating_weighted'] = df['rating'] * df['total_ratings_log']
    df['price_weighted'] = df['price_level_traversed'] * df['total_ratings_log']
    df['price_weighted_filled'] = df['price_level_traversed_filled'] * df['total_ratings_log']


    # scale features according to min-max-normalization
    scaler = MinMaxScaler()

    df['rating_scaled'] = scaler.fit_transform(df['rating'].values.reshape(-1, 1))
    df['price_scaled'] = scaler.fit_transform(df['price_level_traversed'].values.reshape(-1, 1))
    df['smileys_scaled'] = scaler.fit_transform(df['smileys_average_traversed'].values.reshape(-1, 1))
    df['ranking_scaled'] = df[['rating_scaled', 'price_scaled', 'smileys_scaled']].mean(axis=1)

    df['price_scaled_filled'] = scaler.fit_transform(df['price_level_traversed_filled'].values.reshape(-1, 1))
    df['smileys_scaled_filled'] = scaler.fit_transform(df['smileys_average_traversed_filled'].values.reshape(-1, 1))
    df['ranking_scaled_filled'] = df[['rating_scaled', 'price_scaled_filled', 'smileys_scaled_filled']].mean(axis=1)

    df['rating_weighted_scaled'] = scaler.fit_transform(df['rating_weighted'].values.reshape(-1, 1))
    df['price_weighted_scaled'] = scaler.fit_transform(df['price_weighted'].values.reshape(-1, 1))
    df['ranking_weighted_scaled'] = df[['rating_weighted_scaled', 'price_weighted_scaled', 'smileys_scaled']].mean(
        axis=1)

    df['price_weighted_scaled_filled'] = scaler.fit_transform(df['price_weighted_filled'].values.reshape(-1, 1))
    df['ranking_weighted_scaled_filled'] = df[
        ['rating_weighted_scaled', 'price_weighted_scaled_filled', 'smileys_scaled_filled']].mean(axis=1)


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

    cols = ['ranking_scaled_filled', 'ranking_weighted_scaled_filled']
    text = ['Ranking scaled', 'Ranking weighted and scaled']
    for i in range(len(cols)):
        print('TOP PERFORMERS - ' + text[i])
        print('__________________')
        print(df.sort_values(cols[i], ascending=False).head(5))


def map_distribution():
    fig = plt.figure(figsize=(10, 10))
    subplot_positions = [121, 122]

    # plot restaurants geographical distribution
    ax = fig.add_subplot(subplot_positions[0])
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    df_areas.plot(ax=ax, color="lightgrey", edgecolor="darkgrey")
    df.plot(ax=ax, x="longitude", y="latitude", kind="scatter", color='moccasin', alpha=0.5, marker='o', s=20)

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
    # group by city name
    df_cities = df.groupby('city_name').agg({'ref': 'count',
                                             'total_ratings': 'mean',
                                             'total_ratings_log': 'mean',
                                             'rating': 'mean',
                                             'rating_scaled': 'mean',
                                             'price_level': 'mean',
                                             'price_level_filled': 'mean',
                                             'price_scaled': 'mean',
                                             'price_scaled_filled': 'mean',
                                             'no_price': 'sum',
                                             'smileys_average': 'mean',
                                             'smileys_average_filled': 'mean',
                                             'smileys_scaled': 'mean',
                                             'smileys_scaled_filled': 'mean',
                                             'no_smileys': 'sum',
                                             'rating_weighted_scaled': 'mean',
                                             'price_weighted_scaled': 'mean',
                                             'price_weighted_scaled_filled': 'mean',
                                             'ranking_scaled': 'mean',
                                             'ranking_scaled_filled': 'mean',
                                             'ranking_weighted_scaled': 'mean',
                                             'ranking_weighted_scaled_filled': 'mean'}).reset_index()

    df_cities = df_cities.rename(columns={'city_name': 'POSTBYNAVN'})

    # merge with .geojson file
    df_areas_cities = df_areas.merge(df_cities, how='left', on='POSTBYNAVN')

    # plot total ratings per city
    fig = plt.figure(figsize=(15, 15))
    ax = fig.add_subplot(111)
    ax.set_axis_off()
    ax.set_title('Total Rating', fontsize=32)
    df_areas_cities.plot(column='total_ratings', cmap='magma_r', ax=ax, edgecolor='black',
                         missing_kwds={'color': 'lightgray', 'alpha': 0.3, 'hatch': '///', 'edgecolor': 'black',
                                       'linewidth': 0.2}, linewidth=0.2, label='Total Rating')
    plt.savefig('data/cities_map_total_ratings.png')

    # plot features per city
    fig = plt.figure(figsize=(15, 15))
    subplot_positions = [141, 142, 143, 144]
    columns = ['rating_scaled', 'price_scaled_filled', 'smileys_scaled_filled', 'ranking_scaled_filled']
    titles = ['Rating', 'Price Level', 'Smileys', 'Ranking']
    for i in range(len(columns)):
        ax = fig.add_subplot(subplot_positions[i])
        ax.set_axis_off()
        ax.set_title(titles[i], fontsize=22)
        df_areas.plot(column=columns[i], cmap='magma_r', ax=ax, edgecolor='black',
                      missing_kwds={'color': 'lightgray', 'alpha': 0.3, 'hatch': '///', 'edgecolor': 'black',
                                    'linewidth': 0.2}, linewidth=0.2, label=titles[i])
    plt.savefig('data/cities_map_original.png')

    # plot weighted features per city
    fig = plt.figure(figsize=(15, 15))
    subplot_positions = [141, 142, 143, 144]
    columns = ['rating_weighted_scaled', 'price_weighted_scaled_filled', 'smileys_scaled_filled',
               'ranking_weighted_scaled_filled']
    titles = ['Rating Weighted', 'Price Weighted', 'Smileys', 'Ranking Weighted']
    for i in range(len(columns)):
        ax = fig.add_subplot(subplot_positions[i])
        ax.set_axis_off()
        ax.set_title(titles[i], fontsize=22)
        df_areas.plot(column=columns[i], cmap='magma_r', ax=ax, edgecolor='black',
                      missing_kwds={'color': 'lightgray', 'alpha': 0.3, 'hatch': '///', 'edgecolor': 'black',
                                    'linewidth': 0.2}, linewidth=0.2, label=titles[i])
    plt.savefig('data/cities_map_weighted.png')


data_transformation()
general_statistics()
top_performers()
map_distribution()
map_cities()
