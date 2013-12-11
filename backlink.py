#!/usr/bin/env python3
import urllib.request
import urllib.parse
import re
from bs4 import BeautifulSoup as bs

class backlink:
	def __init__(self, url, index, domain):
		self.url = url
		self.sanitized_url = self.url_sanitize(url) 
		self.status = 'UNKNOWN' 
		self.exists = 'EXISTS'
		self.removed = 'REMOVED'
		self.index = index
		self.domain = domain
    
	def url_sanitize(self, url):
		parsed = urllib.parse.urlparse(self.url)
		return urllib.parse.urlunparse(urllib.parse.quote(x) for x in parsed)

	def check_url(self, url):
		req = urllib.request.Request(self.url)
		req.add_header('User-Agent','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.57 Safari/537.36')
		html = urllib.request.urlopen(req).read()
		soup = bs(html)
		link = soup.find_all('a', attrs={'href': re.compile(self.domain)})
		if len(link) > 0: #link from domain was found
			return self.exists 
		else:
			return self.removed 
