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


# getting list of city names (e.g. "Valby", "Frederiksberg" etc.)
def get_city(row):
  if not pd.isnull(row):
    search = re.search('(?<=(, )|^)[^,\d]*?$', row)
    if not pd.isnull(search):
      return search.group(0).title()
    else:
      return np.nan
  else:
    return np.nan


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
    # TODO threshold for sw > 2
    for sw in stopwords:
        if len(name) > 1 and sw in name:
            name.remove(sw)
    name = ' '.join(name)

    # extract street name and number of address to filter out possible 
    # disruptive factors which could restrict the finding of results
    address = place['address']
    city_name = place['city_name']
    if not pd.isnull(address) and address != 'Denmark' and address != 'København':
        try:
            street_name = re.search('(?<=^|, )[^,\n]*[A-Z]+.*?([0-9]+.?[A-Z]?)+(?=,)', address).group(0)
            return name, (street_name + ', ' + city_name)
        except AttributeError:
            return name, city_name
    else:
        return None, None


# check if .csv file with data to be extracted already exists
# (in case the program interrupts and needs to be restarted)
try:
    df_places = pd.read_csv('data/places_combined_enriched_new.csv')
# if not, use basic .csv file
except FileNotFoundError:
    df_places = pd.read_csv('data/places_combined.csv')
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

# extract city names of each entry for removal in name string 
# and additional attribute for later analysis
df_places['city_name'] = df_places['address'].apply(lambda x: get_city(x))
cities = list(df_places['city_name'].value_counts().index)


# iterate through restaurants
for idx, place in df_places.iterrows():
    
    # only work on those entries that have not been investigated yet
    if place['checked_findsmiley'] == 0:
        # extract formatted name and address
        name, address = get_query_string(place)
        
        # if name or address information is given (otherwise it would be 
        # impossible to identify a restaurant)
        if not pd.isnull(name) and not pd.isnull(address):
            
            # enter query string into search box and click on "search"
            input_element = driver.find_element(By.XPATH, '//*[@id="ctl00_PlaceHolderSearchArea_ctl00_csr_sbox"]')
            input_element.send_keys(name + ', ' + address)
            search_button = driver.find_element(By.XPATH, '//*[@id="ctl00_PlaceHolderSearchArea_ctl00_csr_SearchLink"]')
            search_button.click()
            # time.sleep(1)

            try:
                # get restaurant-list element
                restaurant_list = driver.find_element(By.CLASS_NAME, 'ms-srch-group-content').find_elements(By.NAME, "Item")
                best_match_ratio = 0
                best_match_element = ""
                best_match_name = ""
                # get all results for given query string and select that
                # restaurant whose name has highest text similarity
                # compared with "name" 
                for entry in restaurant_list:
                    entry_element = entry.find_element(By.CSS_SELECTOR, "div.template_body.row.smiley_row > table > tbody > tr.search_row_item > td.search_col_1.col-lg-4.col-12.smiley_table > div.template_header > h3 > a")
                    entry_name = entry_element.get_attribute('title')
                    entry_ratio = fuzz.ratio(name.lower(), entry_name.lower())
                    # Only pick those with a sequence similarity of at least 51
                    # (to lower the risk of picking the "wrong" restaurant)
                    if entry_ratio > best_match_ratio and entry_ratio > 50:
                        best_match_element = entry_element
                        best_match_ratio = entry_ratio
                
                if best_match_element == "":
                    raise NoSuchElementException
                best_match_element.click()
                
                smileys, cvr = scrape_smileys_cvr(driver)
                df_places.at[idx, 'smileys'] = smileys
                df_places.at[idx, 'cvr_number'] = cvr if not pd.isnull(cvr) else np.nan
                
            except NoSuchElementException:
                df_places.at[idx, 'smileys'] = np.nan
                df_places.at[idx, 'cvr_number'] = np.nan
                pass
        else:
            df_places.at[idx, 'smileys'] = np.nan
            df_places.at[idx, 'cvr_number'] = np.nan
        
        # reset input field
        input_element = driver.find_element(By.XPATH, '//*[@id="ctl00_PlaceHolderSearchArea_ctl00_csr_sbox"]')
        input_element.clear()
        
        # mark entry as being checked
        df_places.at[idx, 'checked_findsmiley'] = 1
        print(idx, place['name'])

        if idx % 50 == 0:
            print('SAVED')
            df_places.to_csv('data/places_combined_enriched_new.csv')


# save dataframe as .csv file
df_places.to_csv('data/places_combined_enriched_new.csv')



# TODO: merge multiple entries for the same restaurant after extracting all reviews by cvr number
