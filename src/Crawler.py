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


def serialize_document(doc: Document):
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
    doc_path = os.path.join(parent_path, "serialization", "documents", f"{doc.url_hash}.pickle")
    save_pickle(doc, doc_path)


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
    if not os.path.exists(serialisation_folder):
        os.makedirs(serialisation_folder)

    documents_path = os.path.join(serialisation_folder, "documents")
    if not os.path.exists(documents_path):
        os.makedirs(documents_path)


def load_frontier():
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
    serialisation_folder = os.path.join(parent_path, "serialization")
    frontier_path = os.path.join(serialisation_folder, "frontier.pickle")

    if os.path.exists(frontier_path):
        ft = load_pickle(frontier_path)
    else:
        # TODO read default frontier from file
        ft = collections.deque([])
        ft.appendleft("https://uni-tuebingen.de/en/")

    return ft

class Crawler:

    def __init__(self):
        # __crawl_state holds the robots.txt info and other data to check if crawling is allowed for a site
        # for each site (base url) it stores:
        #  - last_crawl: time the site was crawled last
        #  - delay: the crawl delay in seconds for this site
        #  - req_rate: the request rate as tuple of (amount, seconds) for this site
        #  - robots_fp: the robots file parser object to check if a given path is allowed to crawl
        self.__crawl_state = {}

        self.DOC_UPDATE_THRESHOLD = 86400 # after how many seconds should a document be re-fetched
        self.SAME_SITE_THRESHOLD = 100 # after how many crawls for a domain (irr or relevant) should we stop adding links to frontier

    def is_allowed_to_crawl(self, url: str) -> int:
        """
        Checks if the given site is allowed to be crawled. It checks this by looking into the robots.txt file

        returns: 0 if site is not allowed to be crawled
        returns: 1 if site is allowed to be crawled
        returns: 2 if crawl delay or request limit is reached
        """
        now = datetime.today()
        base_url = Document.get_base_url(url)

        if base_url not in self.__crawl_state:
            try:
                robots_fp = Crawler.__get_robots_parser(url)
            except:
                return 0
            self.__add_to_crawl_state(base_url, robots_fp)

        site_crawl_state = self.__crawl_state[base_url]

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
        return 1

    def __add_to_crawl_state(self, base_url: str, robots_fp: RobotFileParser):
        crawl_delay = robots_fp.crawl_delay("*")
        crawl_req_rate = robots_fp.request_rate("*")

        self.__crawl_state[base_url] = {}
        self.__crawl_state[base_url]["last_crawl"] = datetime.today()
        self.__crawl_state[base_url]["robots_fp"] = robots_fp
        self.__crawl_state[base_url]["total_crawls"] = 1

        if crawl_req_rate is not None:
            self.__crawl_state[base_url]["req_rate"] = crawl_req_rate

        if crawl_delay is not None:
            self.__crawl_state[base_url]["delay"] = crawl_delay

    @staticmethod
    def __get_robots_parser(url: str) -> RobotFileParser:
        robots_fp = RobotFileParser()
        robots_fp.set_url(Document.get_base_url(url) + "/robots.txt")
        robots_fp.read()
        return robots_fp

    def __relevant(self, doc: Document):
        return True

    def __language_is_english(self, doc: Document):
        return doc.language == "en"

    def __add_to_frontier(self, url: str) -> bool:
        if self.__crawl_state[Document.get_base_url(url)]["total_crawls"] > self.SAME_SITE_THRESHOLD:
            return False
        return True

    def crawl(self, frontier: collections.deque, document_index: DocumentIndex, print_mode: bool):

        while frontier:
            doc = None
            url = frontier.pop()
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
                if crawl_check == 0:  # disallowed
                    if print_mode: print("not allowed")
                    continue
                elif crawl_check == 2:
                    # if req limit violation put the url at the end of the frontier
                    if print_mode: print("request limit violation")
                    frontier.appendleft(url)
                    continue

                doc = Document(url)
                self.__crawl_state[Document.get_base_url(url)]["total_crawls"] += 1 # keep track of how many times base url was crawled
                if not doc.is_relevant:
                    if print_mode: print("not relevant")
                    continue
                else:
                    # add to frontier even if language is wrong, because we might find english content in links IF content relevant
                    # perform checks in add_to_frontier, so we don't add too much irrelevant links / links in the same domain
                    if self.__add_to_frontier(url):
                        for l in doc.links:
                            frontier.appendleft(l)
                        if print_mode: print("added to frontier")

                # check sim_hashes, if no collision + language is english -> store doc in index
                if not docIndex.has_similar_document(doc) and self.__language_is_english(doc):
                    docIndex.add(doc)
                    if print_mode: print("indexed")
                else:
                    if print_mode: print("not indexed (similar found or wrong language)")

            except Exception as e:
                if print_mode: print("\tError: " + str(e))
                continue
            finally:
                if doc is not None:
                    serialize_document(doc)
                serialize_frontier(frontier)
                serialize_index(document_index)



def load_document_index():
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
    serialisation_folder = os.path.join(parent_path, "serialization")
    index_path = os.path.join(serialisation_folder, "documentIndex.pickle")
    if os.path.exists(index_path):
        return load_pickle(index_path)
    else:
        return DocumentIndex()


if __name__ == '__main__':
    create_folder_structure()

    frontier = load_frontier()
    docIndex = load_document_index()
    crawler = Crawler()
    crawler.crawl(frontier, docIndex, True)
