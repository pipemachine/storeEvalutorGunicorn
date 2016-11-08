import requests

#requests to test the storeEvaluator Flask endpoint
res = requests.post('http://localhost:5000/eval', 
                    json={'url':'https://www.ruvilla.com/',
                          'type_of_crawl':'sniff'
                    })

res = requests.post('http://localhost:5000/eval', 
                    json={'url':'http://www.citysports.com/',
                          'type_of_crawl':'full'
                    })
