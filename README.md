linkcheck
=========

A simple command line tool to check for existence of a backlink to your domain from a list of URLs.  This is for use in cleaning up a spammy back link profile.  Has the option to automatically generate a google disavow.txt file.

As you're working through emailing and documenting your link removal efforts, you can run this every couple days to check progress.  It will crawl each page in a regular text file populated with links, check if there is a link to your domain on the page, and generate a .csv file showing you witch links exist and which are removed.  It can also automatically generate a disavow file based on existing links.

example usage:

linkcheck.py -d example.com -i list_of_urls -o results.csv -w 100 -v -c

The above would check crawl every page in the list_of_urls file for links pointing to example.com and put the results in a file named results.csv.  It would spawn 100 threads to perform the searches (the default is 10 if the -w is not specified), show the output of each URL as it's crawled and generate a domain level disavow file for each domain that has existing links.

sample output:

linkcheck.py -d example.com -i list_of_urls -o results.csv -w 100 -v -c

http://www.foo.com/links: EXISTS
http://www.bar.com/spam: REMOVED
http://www.spammyseofirm.com/webspam: EXISTS

*disavow.txt*
domain:foo.com
domain:spammyseofirm.com
