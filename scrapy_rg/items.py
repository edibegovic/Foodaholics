# -*- coding: utf-8 -*-

"""
@author: lajello

Definitions of the items we are interested in constructing and that the spider will 
fill with the information scraped from the relevant pages. These are mainly wrappers
for dictionary objects, but it is recommended to use item objects instead of dictionaries 
as they integrate seamlessly with different parts of the Scrapy architeture (e.g., pipelines).

REFERENCES:
Items documentation: https://docs.scrapy.org/en/latest/topics/items.html
"""

import scrapy


class ArtistItem(scrapy.Item):
    """
    Item containing information about an artist
    """
    url = scrapy.Field()
    img_url = scrapy.Field()

class BandItem(scrapy.Item):
    """
    Item containing information about a band
    """
    url = scrapy.Field()
    img_url = scrapy.Field()
