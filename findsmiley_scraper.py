from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import numpy as np
import time
import regex as re


# set up webdriver and open page of restaurant
def set_up_driver(URL):
    driver = webdriver.Chrome()
    driver.get(URL)
    time.sleep(2)

    # click on "accept cookies"-button
    cookies_button = driver.find_element(By.XPATH, '//*[@id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')
    cookies_button.click()
    # time.sleep(1)

    return driver


def scrape_smileys_cvr(driver):
    smileys = []
    smiley_table = driver.find_elements(By.TAG_NAME, 'td')
    # search for image url in elite-smiley column
    try:
        # if elite-smiley is given, no other smiley needs to be retrieved (since elite-smiley = 4times 1-smiley)
        smiley_elite_image_url = smiley_table[1].find_element(By.TAG_NAME, 'img').get_attribute('src')
        smiley_elite_value = re.search('(?<=PublishingImages/)(1|2|3|4|Elite)(?=Smiley)', smiley_elite_image_url).group(
            0)
        smileys.append(smiley_elite_value)
    except AttributeError:
        # if not, gather all smiley
        smiley_cols = smiley_table[2].find_elements(By.TAG_NAME, 'span')
        for col in smiley_cols:
            smiley_image_url = col.find_element(By.TAG_NAME, 'a').find_element(By.TAG_NAME, 'img').get_attribute('src')
            if 'kontrolpaaVej' in smiley_image_url:
                # means there are no inspection reports for this restaurant yet
                break
            else:
                try:
                    smiley_value = re.search('(?<=PublishingImages/)(1|2|3|4|Elite)(?=Smiley)', smiley_image_url).group(
                        0)
                    smileys.append(int(smiley_value))
                except:
                    pass

    cvr = driver.find_element(By.XPATH, '//*[@id="Center"]/div/div[2]/div/table/tbody/tr[5]/td[2]').text
    cvr = int(cvr) if cvr != '' else ''

    return smileys, cvr


def get_query_string(place):
    name = place['name']
    address = place['address']

    # format address
    if not pd.isnull(address) and address != 'Denmark' and address != 'København':
        try:
            city_name = re.search('(?<=, )[^,]*?$', place['address']).group(0)
        except AttributeError:
            city_name = address

        try:
            street_name = re.search('(?<=^|, )[^,\n]*(?=( [0-9]+.?[A-Z]?)+,)', address).group(0)
            return name + ', ' + street_name + ', ' + city_name
        except AttributeError:
            return name + ', ' + city_name
    else:
        return None


try:
    df_places = pd.read_csv('data/places_combined_enriched.csv')
except FileNotFoundError:
    df_places = pd.read_csv('data/places_combined.csv')
    df_places['smileys'] = ''
    df_places['cvr_number'] = ''
    df_places['checked_findsmiley'] = 0

# TODO double check for name in restaurant listings on findsmiley.dk before clicking
# TODO to make sure the right restaurant is selected (maybe by using

URL = 'https://findsmiley.dk/Sider/Forside.aspx'
driver = set_up_driver(URL)
for idx, place in df_places.iterrows():

    if place['checked_findsmiley'] == 0:
        query_string = get_query_string(place)

        if not pd.isnull(query_string):

            input_element = driver.find_element(By.XPATH, '//*[@id="ctl00_PlaceHolderSearchArea_ctl00_csr_sbox"]')
            input_element.send_keys(query_string)
            search_button = driver.find_element(By.XPATH, '//*[@id="ctl00_PlaceHolderSearchArea_ctl00_csr_SearchLink"]')
            search_button.click()
            # time.sleep(1)

            try:
                restaurant = driver.find_element(By.XPATH,
                                                 '//*['
                                                 '@id="ctl00_ctl41_g_fd204bb3_400b_4d2e_ae04_031a827050ed_csr2_item'
                                                 '"]/div[1]/table/tbody/tr[1]/td[1]/div[1]/h3/a')
                restaurant.click()
                # time.sleep(1)

                smileys, cvr = scrape_smileys_cvr(driver)
                df_places.at[idx, 'smileys'] = smileys
                df_places.at[idx, 'cvr_number'] = cvr

            except NoSuchElementException:
                df_places.at[idx, 'smileys'] = np.nan
                df_places.at[idx, 'cvr_number'] = np.nan
                pass
        else:
            df_places.at[idx, 'smileys'] = np.nan
            df_places.at[idx, 'cvr_number'] = np.nan

        input_element = driver.find_element(By.XPATH, '//*[@id="ctl00_PlaceHolderSearchArea_ctl00_csr_sbox"]')
        input_element.clear()

        df_places.at[idx, 'checked_findsmiley'] = 1
        print(idx, place['name'])

        if idx % 100 == 0:
            print('SAVED')
            df_places.to_csv('data/places_combined_enriched.csv')

df_places.to_csv('data/places_combined_enriched.csv')

# TODO: merge multiple entries for the same restaurant after extracting all reviews by cvr number
