from urllib.parse import urljoin
from eslog import eslog
from scrapy import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from items import SniffItem
from scrapeProc import html_sniffer
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor

class SniffSpider(Spider):
    name = "sniff"
    esend = eslog('scraped_pages','product')    

    def parse(self, response):
        crawledLinks = []
        # There are often times respones from images, resources, etc that
        # do not result in normal html
        try:
            for link in response.xpath('//a/@href'):
                if link not in crawledLinks:
                    url = link.extract().strip()
                    url = urljoin(self.start_urls[0], url)
                    crawledLinks.append(url)
                    yield Request(url, self.parse)
            item = SniffItem()
            item['url'] = response.url
            isniff = html_sniffer(response.body.decode('utf-8'), self.start_urls[0])
        except (AttributeError, UnicodeDecodeError):
            #print('probably not a normal page. considering adding regex filtering')
            #self.esend.get_health()
            isniff = None
        if isniff:
            try:
                price, title, image = isniff.price_title_image()
            except TypeError:
                #print('probably not a normal page. considering adding regex filtering')
                price = None
            if price and title and image:
                item['price'] = price
                item['title'] = title
                item['image'] = image[0]
                #push item to elastic search
                res = self.esend.push(dict(item))
            yield item

