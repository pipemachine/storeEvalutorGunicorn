import scrapy
from scrapy.crawler import CrawlerRunner
from SniffSpider import SniffSpider
from CrawlSpider import CrawlSpider
from twisted.internet import reactor
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/eval',methods=['GET', 'POST'])
def eval_url():
    """
    Note that this function relies on the flask request context
    The requests.json data dict contains the following parameters
    param: data['type_of_crawl']: 'full' calls CrawlSpider for full crawl
    param: data['url']: the url that dictates allowed_domains and start_url  
    """
    data = request.json
    app.logger.debug(request.json)
    spider = SniffSpider
    if data['type_of_crawl'] == 'full':
        spider = CrawlSpider
    url_to_crawl = data['url']     
    start_urls = [url_to_crawl]
    allowed_domains = [url_to_crawl.split('/')[2]]
    
    runner = CrawlerRunner({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        #'AUTOTHROTTLE_ENABLED' : True,
        'DOWNLAOD_DELAY' : 0.25,
        'ROBOTSTXT_OBEY' : True,
        'LOG_LEVEL' : 'ERROR'
    })
    d = runner.crawl(spider, 
                     start_urls=start_urls, 
                     allowed_domains = allowed_domains)
    d.addBoth(lambda _: reactor.stop())
    reactor.run()
    return jsonify({"complete":True})

if __name__ == '__main__':
    app.run(debug=True)
