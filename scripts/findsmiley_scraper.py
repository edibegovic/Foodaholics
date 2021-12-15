from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import numpy as np
import time
import regex as re
from fuzzywuzzy import fuzz


# set up webdriver and open page findsmiley.dk website
def set_up_driver(URL):
    driver = webdriver.Chrome()
    driver.get(URL)
    time.sleep(2)

    # click on "accept cookies"-button
    cookies_button = driver.find_element(By.XPATH, '//*[@id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')
    cookies_button.click()
    # time.sleep(1)

    return driver


# scrape findsmiley.dk
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


# format name and address to guarantee high quantity and quality of selection
def get_query_string(place):
    # remove city names and stopwords to find as many results as possible
    name = place['name'].split()
    for c in cities:
        if c in name:
            name.remove(c)
    for sw in stopwords:
        if len(name) > 1 and sw in name:
            name.remove(sw)
    name = ' '.join(name)

    # create query string with available elements out of
    # name, street, postal_code, and city_name
    city_name = place['city_name'] if not pd.isnull(place['city_name']) else ""
    if pd.isnull(place['postal_code']) or not pd.isnull(place['postal_code']) and '-' in place['postal_code']:
        postal_code = ""
    else:
        postal_code = place['postal_code']
    if not pd.isnull(place['postal_code']):
        try:
            # extract street name and number of address to filter out possible 
            # disruptive factors which could restrict the finding of results
            # (e.g. 'c/o', 'sal 1' etc.)
            street_name = re.search('(?<=^|, )[^,\n]*[A-Z]+.*?([0-9]+.?[A-Z]?)+(?=,)', place['address']).group(0)
            return name, street_name + ', ' + postal_code + ' ' + city_name
        except (AttributeError, TypeError):
            return name, postal_code + ' ' + city_name
    else:
        try:
            street_name = re.search('(?<=^|, )[^,\n]*[A-Z]+.*?([0-9]+.?[A-Z]?)+(?=,)', place['address']).group(0)
            return name, street_name
        except AttributeError:
            return None, None


# check if .csv file with data to be extracted already exists
# (in case the program interrupts and needs to be restarted)
try:
    df_places = pd.read_csv('data/places_combined_enriched2.csv')
# if not, use basic .csv file
except FileNotFoundError:
    df_places = pd.read_csv('data/places_combined_enriched.csv')
    df_places['smileys'] = ''
    df_places['cvr_number'] = ''
    df_places['checked_findsmiley'] = 0

URL = 'https://findsmiley.dk/Sider/Forside.aspx'
driver = set_up_driver(URL)

# collecting the 30 most common words/tokens in names 
# (e.g. "Restaurant", "&", "ApS", "House") for later stopword removal
token_list = []
for ele in df_places['name']:  # loop over lists in df
    token_list += ele.split()  # append elements of lists to full list
stopwords = list(pd.Series(token_list).value_counts().head(30).index)

# extract city names of each entry for later removal in name-string 
cities = list(df_places['city_name'].unique())

# iterate through restaurants
for idx, place in df_places.iterrows():

    # only work on those entries that have not been investigated yet
    if place['checked_findsmiley'] == 0:
        # extract formatted name and address
        full_name = place['name']
        name, address = get_query_string(place)

        # skip entry if no address is given since it would be vague 
        # to identify a restaurant only by its name
        if pd.isnull(address):
            df_places.at[idx, 'smileys'] = np.nan
            df_places.at[idx, 'cvr_number'] = np.nan
        else:
            if not pd.isnull(name):
                query_string = name + ', ' + address
            elif pd.isnull(name):
                query_string = address
            # enter query string into search box and click on "search"
            input_element = driver.find_element(By.XPATH, '//*[@id="ctl00_PlaceHolderSearchArea_ctl00_csr_sbox"]')
            input_element.send_keys(query_string)
            search_button = driver.find_element(By.XPATH, '//*[@id="ctl00_PlaceHolderSearchArea_ctl00_csr_SearchLink"]')
            search_button.click()
            time.sleep(1)
            try:
                # get restaurant-list element
                restaurant_list = driver.find_element(By.CLASS_NAME, 'ms-srch-group-content').find_elements(By.NAME,
                                                                                                            "Item")
                best_match_element = ""
                best_match_ratio = 0
                # get all results for given query string and select that
                # restaurant whose mean of name and address similarity
                # have highest score compared with "name" and "address"
                for entry in restaurant_list:
                    entry_element = entry.find_element(By.CSS_SELECTOR, "div.template_body.row.smiley_row > table > "
                                                                        "tbody > tr.search_row_item > "
                                                                        "td.search_col_1.col-lg-4.col-12.smiley_table")
                    entry_click_element = entry_element.find_element(By.CSS_SELECTOR, "div.template_header > h3 > a")

                    entry_name = entry_click_element.get_attribute('title')
                    entry_name_ratio = fuzz.ratio(full_name.lower(), entry_name.lower())

                    entry_address = entry_element.find_element(By.CSS_SELECTOR,
                                                               "div:nth-child(2) > p:nth-child(1)").text + ', ' + entry.find_element(
                        By.CSS_SELECTOR, "div:nth-child(2) > p:nth-child(2)").text
                    entry_address_ratio = fuzz.ratio(address.lower(), entry_address.lower())

                    # Only pick those with a sequence similarity of at least 51
                    # as the mean of name and address ratio of restaurant
                    # (to lower the risk of picking the "wrong" restaurant)
                    entry_ratio = np.mean([entry_address_ratio, entry_name_ratio])
                    if entry_ratio > 50 and entry_ratio > best_match_ratio:
                        best_match_element = entry_click_element
                        best_match_ratio = entry_ratio

                if best_match_element == "":
                    raise NoSuchElementException
                # click on the restaurant with the highest match
                best_match_element.click()

                smileys, cvr = scrape_smileys_cvr(driver)
                df_places.at[idx, 'smileys'] = np.nan if len(smileys) == 0 else smileys
                df_places.at[idx, 'cvr_number'] = np.nan if pd.isnull(cvr) or cvr == '' else cvr

            except NoSuchElementException:
                df_places.at[idx, 'smileys'] = np.nan
                df_places.at[idx, 'cvr_number'] = np.nan
                pass

        # reset input field
        input_element = driver.find_element(By.XPATH, '//*[@id="ctl00_PlaceHolderSearchArea_ctl00_csr_sbox"]')
        input_element.clear()

        # mark entry as being checked
        df_places.at[idx, 'checked_findsmiley'] = 1
        print(idx, place['name'])

        if idx % 50 == 0:
            print('SAVED')
            df_places.to_csv('data/places_combined_enriched2.csv')

# save dataframe as .csv file
df_places.to_csv('data/places_combined_enriched2.csv')
