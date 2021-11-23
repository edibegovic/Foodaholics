# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SearchItem(scrapy.Item):
    name = scrapy.Field()
    url = scrapy.Field()

class ReviewItem(scrapy.Item):
    ref = scrapy.Field()
    name = scrapy.Field()
    text = scrapy.Field()
    rating = scrapy.Field()
    lang = scrapy.Field()
    source = scrapy.Field()
    date = scrapy.Field()
    rguru_name = scrapy.Field()
    url = scrapy.Field()

class RestuarantProfile(scrapy.Item):
    name = scrapy.Field()
    reviews = scrapy.Field()