#!/usr/bin/env python3

from queue import Queue
from worker import worker
from backlink import backlink
import csv
import sys
import re
import argparse
import tldextract as tld

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

if ARGS['create-disavow']:
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
