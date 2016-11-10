import redis
from urllib.parse import urljoin
from eslog import eslog
from scrapy import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from items import SniffItem
from scrapeProc import html_sniffer
from scrapy.exceptions import CloseSpider
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor

class SniffSpider(Spider):
    name = "sniff"
    fully_extractable_pages  = 0
    non_extractable_pages  = 0
    elog = eslog('scrape_info','message')    
    red = redis.Redis(host = 'iscrape.snoutsearch.com',port = '6379')

    def parse(self, response):
        crawledLinks = []
        # There are often times respones from images, resources, etc that
        # do not result in normal html
        try:
            for link in response.xpath('//a/@href'):
                if link not in crawledLinks and allowed_domains[0] in link:
                    url = link.extract().strip()
                    url = urljoin(self.start_urls[0], url)
                    crawledLinks.append(url)
                    #purl = 'proxy + url'
                    url  = 'http://64.137.199.141:8050/render.html?url='+url
                    print(url)
                    yield Request(url, self.parse)
            item = SniffItem()
            item['url'] = response.url
            isniff = html_sniffer(response.body.decode('utf-8'), self.start_urls[0])
        except (AttributeError, UnicodeDecodeError):
            #print('probably not a normal page. considering adding regex filtering')
            isniff = None
        if isniff:
            try:
                price, title, image = isniff.price_title_image()
            except TypeError:
                #print('probably not a normal page. considering adding regex filtering')
                price = None
            if price and title and image:
                self.fully_extractable_pages += 1                
                print(price)
                if self.fully_extractable_pages == 10:
                    self.red.sadd('urls_to_scrape',self.start_urls[0])
                    res = self.elog.push({
                                      'msg':'sniffed store and found it scrapable.',
                                      'sucess':True,
                                      'url': self.start_urls[0]
                                       })
                    raise CloseSpider('sufficient_confirmation')
            else:
                non_extractable_pages += 1
                if self.non_extractable_pages > 500:
                    res = self.elog.push({
                                      'msg':'no extractable products found',
                                      'sucess':False,
                                      'url': self.start_urls[0]
                                       })
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
    d = runner.crawl(SniffSpider, start_urls=['http://www.citygear.com/'],allowed_domains = ["citygear.com","64.137.199.141"])
    d.addBoth(lambda _: reactor.stop())
    reactor.run()
