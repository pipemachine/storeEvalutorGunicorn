from datetime import datetime
from elasticsearch import Elasticsearch


class eslog():
    """
    Logging data to AWS elastic search service endpoint
    """
    def __init__(self, index, doc_type):
        """
        param: index: the elastic search index for the logs. Ex: webscraping_logs
        param: doc_type: the elastic search doc_type for logging instance.
                Ex: storeEvaluator
        Initializing elasticsearch client for logging instance.        
        """
        self.es = Elasticsearch([{'host':
            'search-snoutsearch-ndthvbn6x6gjaoskrjsn62b4ea.us-west-2.es.amazonaws.com',
            'port':80
            }])
        self.index = index
        self.doc_type = doc_type

    def get_health(self):
        print(self.es.cluster.health())

    def info(self, data):
        """
        param: data: dict of data to log. minum is to have a log message
        Annotates log INFO level and forwards to send_data to be place in ES
        """
        if data['msg']:
            data['log_level']= "INFO"
            self.send_data(data)
        else:
            print('Please ensure the data is of type dict() with at least a msg')

    def error(self, data):
        """
        param: data: dict of data to log. minum is to have a log message
        Annotates log ERROR level and forwards to send_data to be place in ES
        """
        if data['msg']:
            data['log_level']= "ERROR"
            self.send_data(data)
        else:
            print('Please ensure the data is of type dict() with at least a msg')

    def send_data(self, data):
        """
        param: data: dict of data to log.
        Places time stamp in dict and sends to index/doc_type of the ES endpoint
        """
        data[year]= datetime.now().year
        data[month] =datetime.now().month 
        data[day] =datetime.now().day 
        data[hour] =datetime.now().hour 
        data[minute] =datetime.now().minute 
        data[second] =datetime.now().second 
        res = self.es.index(index=self.index, doc_type=self.doc_type, body=data)        

    def push(self, data):
        """
        param: data: dict of data to log.
        Places time stamp in dict and sends to index/doc_type of the ES endpoint
        """
        print(data)
        res = self.es.index(index=self.index, doc_type=self.doc_type, body=data)        
        print('damn dawg- anything?')
        print(res)
        return res
        
if __name__ == '__main__':
    log = eslog('test_index', 'test_doc_type')
    str(log.get_health())
    print(log.push({'author':'dr_richtermacher'}))

