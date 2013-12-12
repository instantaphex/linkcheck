#!/usr/bin/env python3

from threading import Thread
from queue import Queue
from backlink import backlink
import urllib.error
import http.client
import csv
import sys
import argparse
from operator import itemgetter

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

#Workers
def worker(input_queue, output_queue):
	while True:
		link = input_queue.get()
		if link is None:
			input_queue.task_done()
			input_queue.put(None)
			break
		try:
			link.status = link.check_url(link.url)
		except urllib.error.HTTPError as e:
			link.status = str(e)
		except urllib.error.URLError as e:
			link.status = str(e)
		except http.client.BadStatusLine as e:
			link.status = str(e)
		except UnicodeDecodeError:
			link.check_url(link.sanitized_url)
		except ConnectionResetError:
			input_queue.put(link)
			break
		output_queue.put(link)
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
        if line.strip() != '':
            temp_bl = backlink(line.strip(), number_of_urls, DOMAIN)
        input_queue.put(temp_bl)
        number_of_urls += 1
input_queue.put(None)

#this list will be written to csv after it's sorted
links = []

#Write URL and Status to csv file
with open(OUTFILE, 'a') as f:
	c = csv.writer(f, delimiter=',', quotechar='"')
	for i in range(number_of_urls):
		link = output_queue.get()
		if ARGS['verbose']:
			if link.status == EXISTS:
				print('{}: {}'.format(link.url, PURPLE + link.status + ENDC))
			else:
				print('{}: {}'.format(link.url, ORANGE + link.status + ENDC))
		links.append(link)
		output_queue.task_done()
	links.sort(key=lambda x:x.index)
	for i in links:
		c.writerow((i.index, i.url, i.status))

input_queue.get()
input_queue.task_done()
input_queue.join()
output_queue.join()
