# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SniffItem(scrapy.Item):
    # define the fields for your item here like:
    url = scrapy.Field()
    price = scrapy.Field()
    title = scrapy.Field()
    image = scrapy.Field()
