# -*- coding: utf-8 -*-

"""
@author: lajello

A Scrapy spider to crawl the information about bands and musicians from Wikipedia.
This code was written for teaching purposes. 
If you plan to scrape information from Wikipedia extensively, please be mindful of the additional load
that your process will give to the servers. To match the resources you consume, consider a donation to
the Wikimedia foundation: https://donate.wikimedia.org/

COMMAND:
scrapy crawl wiki [execute this command from the shell]

OPTIONS:
[add these options after the command as needed]
-o result.json [to output all data in a single result file]
-s LOG_FILE=WikiSpider.log [to set a log file]
-s JOBDIR=crawls/wikispider1 [to set persistence status of the crawl, temporary files will be saved in the specified directory]
-a wiki/Ville_Laihiala [an example of url to start the crawl from]
-a ... [any other additional input parameters]

EXAMPLE OF FULL COMMAND:
scrapy crawl wiki_minimal -o result.json -s LOG_FILE=WikiSpider.log -s JOBDIR=crawls/wikispider1 -a start_url=wiki/Ville_Laihiala

REFERENCES:
Scrapy documentation: https://docs.scrapy.org/en/latest/index.html
CSS selectors: https://www.w3schools.com/cssref/css_selectors.asp
Scrapy extension to CSS selectors: https://docs.scrapy.org/en/latest/topics/selectors.html#extensions-to-css-selectors
Xpath syntax: https://www.w3schools.com/xml/xpath_syntax.asp
Xpath cheat sheet: https://devhints.io/xpath
"""

# scrapy library
import scrapy
import logging
from scrapy.utils.trackref import format_live_refs
import pandas as pd
import urllib.parse

# custom class definitions of the items
from ..items import *

class RguruScraper(scrapy.Spider):

    # your spider's name, it must be unique
    name = "rguru_scraper"
    allowed_domains = ["estaurantguru.com", "phet-dev.colorado.edu"]

    def start_requests(self):
        yield scrapy.Request(url='https://phet-dev.colorado.edu/html/build-an-atom/0.0.0-4/simple-text-only-test-page.html', callback=self.scrapeQueue)



    def scrapeQueue(self, response):
        df = pd.read_csv("../data/places_combined_enriched.csv")
        df = df[:200]

        for idx, row in df.iterrows():
            lat, lon = row['location'][1:-1].split(', ')
            name = urllib.parse.quote(row['name'])
            req_url = f'https://restaurantguru.com/search/{name}?sorting=distance&location=-1&geo_point={lat},{lon}'
            yield scrapy.Request(url=req_url, callback=self.parse_results, dont_filter=True, meta={'ref': row['ref']})


    a = 0
    def parse(self, response):
        # create an item to store all the information scraped
        searchItem = SearchItem()

        # use selectors to scrape the image url
        results = response.css('.notranslate.title_url')

        if len(results) > 0:
            name = results[0].css('::text').get()
            url = results[0].css('::attr(href)').get()
            searchItem['name'] = name
            searchItem['url'] = url

            req_url = f'{url}/reviews'
            yield scrapy.Request(url=req_url, callback=self.parse_reviews, dont_filter=True)
            # yield searchItem

    def parse_reviews(self, response):
        reviewItem = ReviewItem()

        # PRINT STAUTS
        self.a += 1
        logging.warning("!!!!!!!!! :D !!!!!!!!!!!!!!!!!!!!!!!!!")
        logging.warning(self.a)

        reviews = response.css('.o_review')

        for review in reviews:
            name = review.css('a::text').get()
            text = review.css('.text_full::text').get()
            rating = review.css('::attr(data-score)').get()
            lang = review.css('::attr(data-lang_id)').get()
            source = review.css('.user_info .grey::text').get()
            rguru_name = response.css('.title_container a::text').get()
            reviewItem['ref'] = response.meta.get('ref')
            reviewItem['name'] = name
            reviewItem['text'] = text
            reviewItem['rating'] = rating
            reviewItem['source'] = source.split()[-1]
            reviewItem['lang'] = lang
            reviewItem['rguru_name'] = rguru_name
            reviewItem['url'] = response.request.url
            yield reviewItem

    def parse_results(self, response):
        # create an item to store all the information scraped
        searchItem = SearchItem()

        # use selectors to scrape the image url
        results = response.css('.notranslate.title_url')

        if len(results) > 0:
            name = results[0].css('::text').get()
            url = results[0].css('::attr(href)').get()
            searchItem['name'] = name
            searchItem['url'] = url

            ref = response.meta.get('ref')
            req_url = f'{url}/reviews'
            yield scrapy.Request(url=req_url, callback=self.parse_reviews, dont_filter=True, meta={'ref': ref})
            # yield searchItem