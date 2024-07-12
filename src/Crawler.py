import os
import sys
from Document import Document
import collections
import pickle
from DocumentIndex import DocumentIndex
from datetime import datetime
from urllib.robotparser import RobotFileParser

sys.setrecursionlimit(50000) # for pickle save


def save_pickle(obj, path):
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def save_text(text, path):
    with open(path, "w", encoding="utf-8") as text_file:
        text_file.write(text)


def serialize_document(doc: Document):
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
    pickle_path = os.path.join(parent_path, "serialization", "documents", "pickle", f"{doc.url_hash}.pickle")
    html_path = os.path.join(parent_path, "serialization", "documents", "html", f"{doc.url_hash}.html")

    save_pickle(doc, pickle_path)
    save_text(doc.raw_html, html_path)


def serialize_frontier(frontier):
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
    serialisation_folder = os.path.join(parent_path, "serialization")
    frontier_path = os.path.join(serialisation_folder, "frontier.pickle")
    save_pickle(frontier, frontier_path)


def serialize_index(document_index):
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
    serialisation_folder = os.path.join(parent_path, "serialization")
    index_path = os.path.join(serialisation_folder, "documentIndex.pickle")
    save_pickle(document_index, index_path)


def create_folder_structure():
    # create folder for documents
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))

    serialisation_folder = os.path.join(parent_path, "serialization")
    documents_path1 = os.path.join(serialisation_folder, "documents", "pickle")
    documents_path2 = os.path.join(serialisation_folder, "documents", "html")

    for p in [serialisation_folder, documents_path1, documents_path2]:
        if not os.path.exists(p):
            os.makedirs(p)


def load_frontier():
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
    serialisation_folder = os.path.join(parent_path, "serialization")
    frontier_path = os.path.join(serialisation_folder, "frontier.pickle")

    if os.path.exists(frontier_path):
        ft = load_pickle(frontier_path)
    else:
        ft = collections.deque([])
        file = open("start_frontier.txt", "r")
        for line in file:
            if not line.startswith('#'):
                ft.appendleft(line.rstrip('\n'))
        file.close()
    return ft


def load_document_index():
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
    serialisation_folder = os.path.join(parent_path, "serialization")
    index_path = os.path.join(serialisation_folder, "documentIndex.pickle")
    if os.path.exists(index_path):
        return load_pickle(index_path)
    else:
        return DocumentIndex()


class Crawler:

    def __init__(self):
        # __crawl_state holds the robots.txt info and other data to check if crawling is allowed for a domain
        # for each site (base url) it stores:
        #  - last_crawl: time the domain was crawled last
        #  - delay: the crawl delay in seconds for this domain
        #  - req_rate: the request rate as tuple of (amount, seconds) for this domain
        #  - robots_fp: the robots file parser object to check if a given path is allowed to crawl
        #  - total_crawls: the amount of pages that were crawled, incremented for each new crawl
        #  - irrelevancy_counter: the amount of crawls for a domain that had no relevant content. This is reset if a relevant page is found (before the maximum is reached)
        self.__crawl_state = {}

        self.DOC_UPDATE_THRESHOLD = 86400       # after how many seconds should a document be re-fetched
        self.SAME_SITE_THRESHOLD = 100          # after how many crawls for a domain should we stop adding links to frontier
        self.SITE_IRRELEVANCY_THRESHOLD = 100   # after how many CONSECUTIVE irrelevant crawls for a domain should we remove the domain from frontier

    # for debugging
    def __pretty_print_crawl_state(self):
        for domain, state in self.__crawl_state.items():
            print(domain)
            for key, value in state.items():
                if key != "robots_fp":
                    print(f"\t{key}:  {str(value)}")

    def is_allowed_to_crawl(self, url: str) -> int:
        """
        Checks if the given site is allowed to be crawled and updates the attributes.
        It checks this by looking into the robots.txt file

        returns: 0 if site is not allowed to be crawled
        returns: 1 if site is allowed to be crawled
        returns: 2 if crawl delay or request limit is reached
        returns: 3 if maximum amount of crawls for the domain is reached
        returns: 4 if the maximum amount of irrelevant crawls for the domain is reached
        """
        now = datetime.today()
        domain = Document.get_domain(url)

        if domain not in self.__crawl_state:
            try:
                robots_fp = Crawler.__get_robots_parser(url)
            except:
                return 0
            self.__add_to_crawl_state(domain, robots_fp)

        site_crawl_state = self.__crawl_state[domain]

        if site_crawl_state.get("total_crawls", 0) >= self.SAME_SITE_THRESHOLD:
            return 3

        if site_crawl_state.get("irrelevancy_counter", 0) >= self.SITE_IRRELEVANCY_THRESHOLD:
            return 4

        # if crawling for this site (and path) is disallowed
        robots_fp = site_crawl_state["robots_fp"]
        if not robots_fp.can_fetch("*", url):
            return 0

        # else check the delay or request limit
        last_crawl = site_crawl_state.get("last_crawl", None)
        sec_since_last_crawl = max((now - last_crawl).total_seconds(), 0)

        delay = site_crawl_state.get("delay", None)
        if delay is not None and last_crawl is not None:
            if sec_since_last_crawl < delay:
                return 2

        req_rate = site_crawl_state.get("req_rate", None)
        if req_rate is not None:
            amount_fetched = site_crawl_state.get("amount_fetched", 0)
            max_requests, time_period_sec = req_rate

            if sec_since_last_crawl > time_period_sec:
                site_crawl_state["amount_fetched"] = 0
            elif amount_fetched < max_requests and sec_since_last_crawl < time_period_sec:
                site_crawl_state["amount_fetched"] = site_crawl_state.get("amount_fetched", 0) + 1
            else:
                return 2

        site_crawl_state["last_crawl"] = now
        site_crawl_state["total_crawls"] = site_crawl_state.get("total_crawls", 0) + 1
        return 1

    def __add_to_crawl_state(self, domain: str, robots_fp: RobotFileParser):
        crawl_delay = robots_fp.crawl_delay("*")
        crawl_req_rate = robots_fp.request_rate("*")

        self.__crawl_state[domain] = {}
        self.__crawl_state[domain]["last_crawl"] = datetime.today()
        self.__crawl_state[domain]["robots_fp"] = robots_fp
        self.__crawl_state[domain]["total_crawls"] = 0
        self.__crawl_state[domain]['irrelevancy_counter'] = 0

        if crawl_req_rate is not None:
            self.__crawl_state[domain]["req_rate"] = crawl_req_rate

        if crawl_delay is not None:
            self.__crawl_state[domain]["delay"] = crawl_delay

    @staticmethod
    def __get_robots_parser(url: str) -> RobotFileParser:
        robots_fp = RobotFileParser()
        robots_fp.set_url(Document.get_base_url(url) + "/robots.txt")
        robots_fp.read()
        return robots_fp

    def __add_links_to_frontier(self, url: str, links: list):
        if self.__crawl_state[Document.get_domain(url)]["total_crawls"] < self.SAME_SITE_THRESHOLD:
            for l in links:
                frontier.appendleft(l)

    def crawl(self, frontier: collections.deque, document_index: DocumentIndex, print_mode: bool, expand_doc: bool):

        while frontier:
            doc = None
            url = frontier.pop()
            domain = Document.get_domain(url)
            if print_mode: print(url, end="\t")

            # check if url already crawled
            if document_index.has_doc(url):
                #check how long since last crawl
                last_crawl = document_index.get_doc_index(url)["last_crawled"]
                time_since_last_crawl = max((datetime.today() - last_crawl).total_seconds(), 0)
                if time_since_last_crawl < self.DOC_UPDATE_THRESHOLD:
                    if print_mode: print("last crawled threshold not met")
                    continue

            try:
                # check crawl rule of robots.txt
                crawl_check = self.is_allowed_to_crawl(url)

                if crawl_check == 0:    # disallowed
                    if print_mode: print("not allowed")
                    continue
                elif crawl_check == 2:  # if req limit violation put the url at the end of the frontier
                    if print_mode: print("request limit violation")
                    frontier.appendleft(url)
                    continue
                elif crawl_check == 3:  # remove the urls with same domain from the frontier
                    if print_mode: print(f"maximum crawl amount for {domain} reached, removing all links from this domain")
                    for link in [u for u in frontier if Document.get_domain(u) == domain]:
                        frontier.remove(link)
                    continue
                elif crawl_check == 4:  # remove the urls with same domain from the frontier
                    if print_mode: print(f"maximum irrelevancy counter for {domain} reached, removing all links from this domain")
                    for link in [u for u in frontier if Document.get_domain(u) == domain]:
                        frontier.remove(link)
                    continue

                doc = Document(url, expand_doc)

                # check sim_hashes, if no collision + language is english and doc related to Tü -> store doc in index
                if not doc.is_relevant:
                    self.__crawl_state[domain]['irrelevancy_counter'] = self.__crawl_state[domain].get("irrelevancy_counter", 0) + 1
                    if print_mode: print(f"document not relevant, irrelevancy_counter for domain: {self.__crawl_state[domain]['irrelevancy_counter']}")
                    continue
                elif docIndex.has_similar_document(doc):
                    if print_mode: print("similar document found")
                    continue

                # SITE RELEVANT
                docIndex.add(doc)
                self.__add_links_to_frontier(url, doc.links)

                # reset the irrelevancy_counter
                self.__crawl_state[domain]['irrelevancy_counter'] = 0
                if print_mode:
                    print("indexed + added to frontier")

                # self.__pretty_print_crawl_state()
            except Exception as e:
                if print_mode: print("\tError: " + str(e))
                # raise e
                continue
            finally:
                if doc is not None:
                    serialize_document(doc)
                serialize_frontier(frontier)
                serialize_index(document_index)


if __name__ == '__main__':
    create_folder_structure()

    frontier = load_frontier()
    docIndex = load_document_index()
    crawler = Crawler()
    crawler.crawl(frontier, docIndex, print_mode=True, expand_doc=True)
