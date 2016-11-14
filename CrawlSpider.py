import random
import redis
from urllib.parse import urljoin
from eslog import eslog
from scrapy import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from items import SniffItem
from scrapeProc import html_sniffer
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor

class CrawlSpider(Spider):
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
                    #allowed domains include splash proxies, so we have to filter
                    if self.start_urls[0] not in url:
                        crawledLinks.append(url)
                    else:
                        rand = random.randint(0,len(self.allowed_domains)-2)
                        splashIP = self.allowed_domains[rand]
                        url = 'http://{0}:8050/render.html?url={1}'.format(splashIP,url)
                        yield Request(url, self.parse)
            item = SniffItem()
            item['url'] = response.url.split("url=")[1]
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
            if price and title and 'http' in image[0]:
                item['price'] = price
                item['title'] = title
                item['image'] = image[0]
                #push item to elastic search
                res = self.esend.push(dict(item))
            yield item

if __name__ == '__main__':
    red = redis.Redis(host = 'iscrape.snoutsearch.com',port = '6379')
    runner = CrawlerRunner({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        #'AUTOTHROTTLE_ENABLED' : True,
        'DOWNLAOD_DELAY' : 0.25,
        'ROBOTSTXT_OBEY' : True,
        'LOG_LEVEL' : 'ERROR'
    })
    newurl = red.spop('urls_to_scrape').decode('utf-8')
    start_urls = [newurl]
    with open('splashNodes') as f:
        nodeURLs = f.readlines()
    domains = [x.replace('\n','') for x in nodeURLs]
    domains.append(newurl.split('/')[2])
    d = runner.crawl(CrawlSpider, start_urls=start_urls,allowed_domains = domains)
    d.addBoth(lambda _: reactor.stop())
    reactor.run()
