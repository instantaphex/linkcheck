#!/usr/bin/env python3

from threading import Thread
from queue import Queue
import urllib.request
import urllib.parse
import urllib.error
import csv
import re
import sys
import argparse
from bs4 import BeautifulSoup as bs

parser = argparse.ArgumentParser(description='Check list of URLs for existence of link in html')
parser.add_argument('-d','--domain', help='The domain you would like to search for a link to', required=True)
parser.add_argument('-i','--input', help='Text file with list of URLs to check', required=True)
parser.add_argument('-o','--output', help='Named of csv to output results to', required=True)
parser.add_argument('-v','--verbose', help='Display URLs and statuses in the terminal', required=False, action='store_true')

ARGS = vars(parser.parse_args())
INFILE = ARGS['input']
OUTFILE = ARGS['output']
DOMAIN = ARGS['domain']
REMOVED = 'REMOVED'
EXISTS = 'EXISTS'
MANUAL = 'MANUAL'
NUMBER_OF_WORKERS = 50 
PURPLE = '\033[95m'
ORANGE = '\033[91m'
BOLD = '\033[1m'
ENDC = '\033[0m'

def url_sanitize(url):
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse(urllib.parse.quote(x) for x in parsed)

def check_url(url):
    req = urllib.request.Request(url)
    req.add_header('User-Agent','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.57 Safari/537.36') #act natural...
    html = urllib.request.urlopen(req).read()
    soup = bs(html)
    link = soup.find_all('a', attrs={'href': re.compile(DOMAIN)})
    if len(link) > 0: #link from domain was found
        return EXISTS
    else:
        return REMOVED

#Workers
def worker(input_queue, output_queue):
    while True:
        url = input_queue.get()
        if url is None:
            input_queue.task_done()
            input_queue.put(None)
            break
        try:
            status = check_url(url)
        except urllib.error.HTTPError as e:
            status = str(e)
        except urllib.error.URLError as e:
            status = str(e)
        except UnicodeDecodeError:
            check_url(url_sanitize(url))
        output_queue.put((url, status))
        input_queue.task_done()

#Queues
input_queue = Queue()
output_queue = Queue()

#Create threads
for i in range(NUMBER_OF_WORKERS):
    t = Thread(target=worker, args=(input_queue, output_queue))
    t.daemon = True
    t.start()

#Populate input queue
number_of_urls = 0
with open(INFILE, 'r') as f:
    for line in f:
        input_queue.put(line.strip())
        number_of_urls += 1
input_queue.put(None)

#Write URL and Status to csv file
with open(OUTFILE, 'a') as f:
    c = csv.writer(f, delimiter=',', quotechar='"')
    for i in range(number_of_urls):
        url, status = output_queue.get()
        if ARGS['verbose']:
            if status == EXISTS:
                print('{} {}'.format(url, PURPLE + status + ENDC))
            else:
                print('{} {}'.format(url, ORANGE + status + ENDC))
        c.writerow((url, status))
        output_queue.task_done()

input_queue.get()
input_queue.task_done()
input_queue.join()
output_queue.join()
