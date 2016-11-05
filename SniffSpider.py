from urllib.parse import urljoin
from scrapy import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from items import SniffItem
from scrapeProc import html_sniffer
from scrapy.exceptions import CloseSpider
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor
import redis

class SniffSpider(Spider):
    name = "sniff"
    fully_extractable_pages  = 0
    non_extractable_pages  = 0
    red = redis.Redis(host='iscrape.snoutsearch.com',port='6379')

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
            print('probably not a normal page. considering adding regex filtering')
            isniff = None
        if isniff:
            try:
                price, title, image = isniff.price_title_image()
            except TypeError:
                print('probably not a normal page. considering adding regex filtering')
                price = None
            if price and title and image:
                self.fully_extractable_pages += 1                
                print('EXTRACTABLE: {0}'.format(self.fully_extractable_pages))
                if self.fully_extractable_pages > 10:
                    print('This domain has extractable products on it.')
                    #toss into a redis queue for full scraping and log
                    self.red.sadd('domains_to_scrape',self.start_urls[0])
                    raise CloseSpider('sufficient_confirmation')
                item['price'] = price
                item['title'] = title
                item['image'] = image
                print(item)
            else:
                non_extractable_pages += 1
                if self.non_extractable_pages > 500:
                    print('This domain does not have extractable products on it.')
                    #toss into a redis list for failures and log
                    raise CloseSpider('sufficient_confirmation')
            yield item


if __name__ == '__main__':
    runner = CrawlerRunner({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        #'AUTOTHROTTLE_ENABLED' : True,
        'DOWNLAOD_DELAY' : 0.25,
        'ROBOTSTXT_OBEY' : True,
        'LOG_LEVEL' : 'ERROR'
    })
    d = runner.crawl(SniffSpider, start_urls=['http://www.citygear.com/'],allowed_domains = ["citygear.com"])
    d.addBoth(lambda _: reactor.stop())
    reactor.run()
