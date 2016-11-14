import scrapy
import os
import subprocess
import time


def runFork():
    while True:
        for i in range(1,4):
            subprocess.Popen(['python3.5','SniffSpider.py'])
        time.sleep(180)
        subprocess.Popen(['python3.5','CrawlSpider.py'])
        time.sleep(300)

if __name__ == "__main__":
    runFork()
