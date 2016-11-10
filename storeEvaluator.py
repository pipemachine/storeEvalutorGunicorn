import scrapy
import multiprocessing
import redis
from scrapy.crawler import CrawlerRunner
from SniffSpider import SniffSpider
from CrawlSpider import CrawlSpider
from twisted.internet import reactor

def eval_url(arg_dict):
    """
    Note that this function relies on the flask request context
    The requests.json data dict contains the following parameters
    param: data['type_of_crawl']: 'full' calls CrawlSpider for full crawl
    param: data['url']: the url that dictates allowed_domains and start_url  
    """
    spider = SniffSpider
    if arg_dict['crawl_type'] == 'full':
        spider = CrawlSpider
    url_to_crawl = arg_dict['url']     
    start_urls = [url_to_crawl]
    runner = CrawlerRunner({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        #'AUTOTHROTTLE_ENABLED' : True,
        'DOWNLAOD_DELAY' : 0.25,
        'ROBOTSTXT_OBEY' : True,
        'LOG_LEVEL' : 'ERROR'
    })
    with open('splashNodes') as f:
            nodeURLs = f.readlines()
    domains = [x.replace('\n','') for x in nodeURLs]
    domains.append(url_to_crawl.split('/')[2])
    d = runner.crawl(spider, start_urls=start_urls,allowed_domains = domains)
    d.addBoth(lambda _: reactor.stop())
    reactor.run()
    return 'in there'

if __name__ == "__main__":
    red = redis.Redis(host='iscrape.snoutsearch.com',port='6379') 
    while True:
        newurl = red.spop('urls_to_eval').decode('utf-8')
        if newurl:
            print('grabbed {0}'.format(newurl))
            arg_dict = {'url':newurl,'crawl_type':"sniff"}
            p = multiprocessing.Process(target=eval_url,args=(arg_dict,))
            p.start()
