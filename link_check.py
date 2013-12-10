#!/usr/bin/env python3
import urllib.request
import urllib.parse
import sys
import re
import csv
from bs4 import ResultSet
from bs4 import BeautifulSoup

DOMAIN = sys.argv[1]
LIST = sys.argv[2]
sheet = csv.writer(open('bs_test.csv', 'w'), delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
PURPLE = '\033[95m'
ORANGE = '\033[91m'
BOLD = '\033[1m'
ENDC = '\033[0m'
def url_sanitize(url):
	parsed = urllib.parse.urlparse(url)
	return urllib.parse.urlunparse(urllib.parse.quote(x) for x in parsed)

def check_url(url):
	url_exists = False
	req = urllib.request.Request(url)
	req.add_header('User-Agent','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.57 Safari/537.36')
	html = urllib.request.urlopen(req).read()
	soup = BeautifulSoup(html)
	link = soup.find_all('a', attrs={'href': re.compile(DOMAIN)})
	if len(link) > 0:
		print(BOLD + url + ENDC, PURPLE +  'EXISTS' + ENDC)
		sheet.writerow([url, 'EXISTS'])
	else:
		print(BOLD + url + ENDC, ORANGE + 'REMOVED' + ENDC)
		sheet.writerow([url, 'REMOVED'])
				

with open(LIST, "r") as f:
	for line in f:
		try:
			line = line.strip('\n')
			check_url(line)
		except KeyboardInterrupt:
			raise
		except urllib.error.HTTPError as e:
			print(BOLD + url_sanitize(line) + ENDC, ORANGE + str(e) + ENDC)
			sheet.writerow([line, e])
		except urllib.error.URLError as e:
			print(BOLD + url_sanitize(line) + ENDC, ORANGE + str(e) + ENDC)
			sheet.writerow([line, e])
		except KeyError:
			print(BOLD + line + ENDC, ORANGE + 'REMOVED' + ENDC)
			sheet.writerow([line, 'REMOVED'])
		except UnicodeDecodeError:
			check_url(url_sanitize(line))
