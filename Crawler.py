import requests, time, random, os, logging
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
import pandas

# Read frontier
# [Index, Link, Last Crawled]

# If no frontier available, load original frontier from csv
if (os.path.exists("frontier.pkl")):
	frontier = read_pickle("frontier.pkl")
else if (os.path.exists("initial_frontier.csv")):
	frontier = read_csv("initial_frontier.csv")
else:
	print("No initial frontier.")

for index, row in frontier.iterrows():
	# Check if we should craw:
		# Last Crawl == None: always crawl
		# Last Crawl <= Treshhold: crawl
		# else no crawl

	# if crawl:
		# follow robots.txt rules
		# if check_relevance():
		# Find_links()
		# add Links to Frontier (no duplicates)
		# pickle df periodically