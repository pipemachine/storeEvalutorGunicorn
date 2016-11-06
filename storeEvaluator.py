import scrapy
from scrapy.crawler import CrawlerRunner
from SniffSpider import SniffSpider
from twisted.internet import reactor
from flask import Flask, request, jsonify
app = Flask(__name__)

    # master node should regulate what gets pushed to the flask enpoint
    #url_to_crawl = str(red.spop('urls_to_evaluate'),'utf-8')
@app.route('/eval',methods=['GET', 'POST'])
def eval_url():
    content = request.json
    app.logger.debug(request.json)
    url_to_crawl = content['url']     
    start_urls = [url_to_crawl]
    allowed_domains = [url_to_crawl.split('/')[2]]
    
    runner = CrawlerRunner({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        #'AUTOTHROTTLE_ENABLED' : True,
        'DOWNLAOD_DELAY' : 0.25,
        'ROBOTSTXT_OBEY' : True,
        'LOG_LEVEL' : 'ERROR'
    })
    d = runner.crawl(SniffSpider, start_urls=start_urls, allowed_domains = allowed_domains)
    d.addBoth(lambda _: reactor.stop())
    reactor.run()
    return jsonify({"complete":True})

if __name__ == '__main__':
    app.run(debug=True)
