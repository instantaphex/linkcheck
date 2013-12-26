#!/usr/bin/env python3

from queue import Queue
import csv
import sys
import re
import argparse
import urllib.error
import urllib.parse
import urllib.request
import http.client
from time import sleep
import tldextract as tld
from threading import Thread
from bs4 import BeautifulSoup as bs

parser = argparse.ArgumentParser(description='Check list of URLs for existence of link in html')
parser.add_argument('-d','--domain', help='The domain you would like to search for a link to', required=True)
parser.add_argument('-i','--input', help='Text file with list of URLs to check', required=True)
parser.add_argument('-o','--output', help='Named of csv to output results to', required=True)
parser.add_argument('-v','--verbose', help='Display URLs and statuses in the terminal', required=False, action='store_true')
parser.add_argument('-w','--workers', help='Number of workers to create', nargs='?', default='10', required=False)
parser.add_argument('-c','--createdisavow', help='Create disavow.txt file for Google disavow links tool', required=False, action='store_true')

ARGS = vars(parser.parse_args())
INFILE = ARGS['input']
OUTFILE = ARGS['output']
DOMAIN = ARGS['domain']
NUMBER_OF_WORKERS = int(ARGS['workers']) 
VERBOSE = ARGS['verbose']
CREATE_DISAVOW = ARGS['createdisavow']
PURPLE = '\033[95m'
ORANGE = '\033[91m'
BOLD = '\033[1m'
ENDC = '\033[0m'

class backlink:
	def __init__(self, url, index, domain):
		self.url = url
		self.status = 'UNKNOWN' 
		self.index = index
		self.domain = domain
    
class worker(Thread):
	def __init__(self, input_queue, output_queue, domain):
		super(worker, self).__init__()
		self.daemon = True
		self.cancelled = False
		self.input_queue = input_queue
		self.output_queue = output_queue
		self.domain = domain

	def url_sanitize(self, url):
		parsed = urllib.parse.urlparse(url)
		return urllib.parse.urlunparse(urllib.parse.quote(x) for x in parsed)

	def check_url(self, url):
		req = urllib.request.Request(url)
		req.add_header('User-Agent','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.57 Safari/537.36')
		try:
			html = urllib.request.urlopen(req).read()
		except urllib.error.HTTPError as e:
			html = e.read()
		soup = bs(html)
		link = soup.find_all('a', attrs={'href': re.compile(self.domain)})
		if len(link) > 0: #link from domain was found
			return 'EXISTS'
		else:
			return 'REMOVED'

	#Workers
	def run(self):
		while not self.cancelled:
			link = self.input_queue.get()
			if link is None:
				self.input_queue.task_done()
				self.input_queue.put(None)
				break
			try:
				link.status = self.check_url(link.url)
			except urllib.error.HTTPError as e:
				link.status = str(e)
			except urllib.error.URLError as e:
				link.status = str(e)
			except http.client.BadStatusLine as e:
				link.status = str(e)
			except UnicodeDecodeError:
				self.check_url(self.sanitize_url(link.url))
			except ConnectionResetError:
				input_queue.put(link)
				break
			self.output_queue.put(link)
			self.input_queue.task_done()
			sleep(0.01)

	def cancel(self):
		self.cancelled = True



#Queues
input_queue = Queue()
output_queue = Queue()

#Create threads
for i in range(NUMBER_OF_WORKERS):
	t = worker(input_queue, output_queue, DOMAIN) 
	t.start()

#Populate input queue
number_of_urls = 0
with open(INFILE, 'r') as f:
    for line in f:
        if line.strip() != '':
            temp_bl = backlink(line.strip(), number_of_urls, DOMAIN)
        input_queue.put(temp_bl)
        number_of_urls += 1
input_queue.put(None)

#this list will be written to csv after it's sorted
links = []
disavow_links = []
#Write URL and Status to csv file
with open(OUTFILE, 'a') as f:
	c = csv.writer(f, delimiter=',', quotechar='"')
	for i in range(number_of_urls):
		link = output_queue.get()
		if VERBOSE:
			if link.status == 'EXISTS':
				print('{}: {}'.format(link.url, PURPLE + link.status + ENDC))
				#populate list for disavow file
				if CREATE_DISAVOW:
					dom = tld.extract(link.url)
					disavow_links.append('domain:' + dom.domain + '.' + dom.suffix + '\n')
			else:
				print('{}: {}'.format(link.url, ORANGE + link.status + ENDC))
		links.append(link)
		output_queue.task_done()
	links.sort(key=lambda x:x.index)
	for i in links:
		c.writerow((i.index, i.url, i.status))

if CREATE_DISAVOW:
	#remove duplicates from disavow_links list
	disavow_links = set(disavow_links)

	#write disavow.txt file
	with open('disavow.txt', 'w') as f:
		for i in disavow_links:
			f.write(i)

input_queue.get()
input_queue.task_done()
input_queue.join()
output_queue.join()
