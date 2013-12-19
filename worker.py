#!/usr/bin/env python3
from queue import Queue
from threading import Thread
from backlink import backlink
import urllib.error
import urllib.parse
import urllib.request
import http.client
from time import sleep
import re
from bs4 import BeautifulSoup as bs

class worker(Thread):
	def __init__(self, input_queue, output_queue):
		super(worker, self).__init__()
		self.daemon = True
		self.cancelled = False
		self.input_queue = input_queue
		self.output_queue = output_queue

	def url_sanitize(self, url):
		parsed = urllib.parse.urlparse(url)
		return urllib.parse.urlunparse(urllib.parse.quote(x) for x in parsed)

	def check_url(self, url):
		req = urllib.request.Request(url)
		req.add_header('User-Agent','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.57 Safari/537.36')
		html = urllib.request.urlopen(req).read()
		soup = bs(html)
		link = soup.find_all('a', attrs={'href': re.compile(url)})
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
