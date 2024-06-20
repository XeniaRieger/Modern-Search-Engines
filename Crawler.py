import os
import datetime
from bs4 import BeautifulSoup
from pathlib import Path
import pandas

# Initial frontier structure (csv file):
# [Num, Link]
# Frontier while crawling (pandas df):
# [Num, Link, Last crawled, Irrelevant Counter]

# Index structure:
# save documents as Num.txt in documents folder
# pandas df: [Num, Link, Last updated, Hash]

# If no frontier available, load original frontier from csv
try:
	frontier = read_pickle("frontier.pkl")
	try:
		index = read_pickle("index.pkl")
		last_identifier = len(index)
	except:
		print("Index missing.")
except:
	try:
		(os.path.exists("initial_frontier.csv")):
		frontier = read_csv("initial_frontier.csv", names=["num", "link"])
		frontier["last_crawl"] = None
		frontier["irr_counter"] = 0
		index = pd.DataFrame({"num":[], "link":[], "last_update":[], "hash":[]})
		last_identifier = 0
	except:
		print("Frontier missing.")

frontier_queue = queue.Queue()
for index, row in frontier.iterrows():
	frontier_queue.put(row[0])

# TODO @Xenia if no update for longer time put items from index into frontier to update

# save index documents in seperate folder
folder_name = os.getcwd() + '/documents'
Path(folder_name).mkdir(exist_ok=True)

while (!frontier_queue.empty()):
	# TODO (@Frauke?) check delay robots.txt, pass link if not allowed to crawl, but do not remove from frontier?
	link_num = frontier_queue.get()
	link = frontier.loc[frontier["num"]==link_num]["link"]
	try:
		# TODO @Xenia if link in index and recently updated we don't have to index again
		# load website
		response = urllib2.urlopen(link)
    	html_doc = response.read()
    	soup = BeautifulSoup(html_doc, 'html.parser')
		# relevant = related to Tübingen (any language is counted as relevant)
		rel = relevant(soup)
		# always add links to frontier, they get discarded after to many nested irrelevant documents
		irrelevant_threshold = 5
		if rel:
			irr = 0
		else:
			irr = 1
		if frontier.loc[frontier["num"]==link_num]["irr_counter"] + irr < irrelevant_threshold:
			add_to_frontier(get_links(soup))
		# index if relevant
		# TODO @Andreas / @Lars only index in language is english
		if rel:
			# TODO @Lars check hash for duplicates to exclude (very) similar documents
			last_identifier += 1
			index = pd.concat([pd.DataFrame([[last_identifier, 
											  link]],
											  datetime.now(),
											  hash(doc), # TODO @Lars
											  columns=index.columns), index], ignore_index=True)
			file = open(folder_name + "/" + last_identifier + ".txt", mode='a', encoding='utf-8')
			file.write("test") # TODO @Xenia or @Lars
		except:
			print("Error occured for link " link_num + ": " + link)
        	print(e)

# gets: soup object from Beutiful Soup, i.e. parsed website
# returns: boolean
# TODO @Andreas
def relevant(soup):

# gets: soup object from Beutiful Soup, i.e. parsed website; url of visted website
# returns: list of full links on a website
# TODO @Andreas
def get_links(soup, url):
    strhtm = soup.prettify()
    #print("Website hat Sprache: " + detect(strhtm))
    a_tags = soup.find_all("a", href=True)
    hrefs = []

    for a in a_tags:
        href = a.get('href')  
        if is_external(href):
            hrefs.append(href)

        else: # TODO aktuell noch falsch! man bekommt links mit Doppelungen z.B. en in 'https://uni-tuebingen.de/en/en/#ut-identifier--main-nav'. siehe get_base_url  
            hrefs.append(url + href)


    return hrefs

def is_external(url):
    return url.startswith(('www', 'http', 'https')) # TODO @Andreas add other rules if needed

# returns: reduced url to scheme and domain, e.g. https://uni-tuebingen.de/en/ -> https://uni-tuebingen.de
# TODO @Andreas or @Frauke?
def get_base_url(url):
    pass

def add_to_frontier(links):
	# TODO @Frauke check robots.txt to exclude links
	# TODO @Xenia check for duplicates in frontier
