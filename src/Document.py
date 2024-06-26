from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import hashlib
import nltk
import langdetect
from datetime import datetime
from Tokenizer import tokenize


class Document:

    def __init__(self, url: str):
        self.url = url
        self.url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        self.soup = None
        self.sim_hash = None
        self.language = None
        self.description = None
        self.tokens = None
        self.links = []
        self.last_crawled = None
        self.is_relevant = None

        # fetch document content and store the relevant information
        self.__fetch_document_content()

    def __fetch_document_content(self):

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        res = requests.get(self.url, headers=headers)
        if res.status_code != 200:
            raise Exception("Request failed with status: " + str(res.status_code))

        self.soup = BeautifulSoup(res.text, 'html.parser')

        # remove script and style elements
        for script in self.soup(["script", "style"]):
            script.decompose()

        self.tokens = self.__tokenize_document()
        self.language = self.__detect_document_language()
        self.links = self.__get_links()

        self.description = self.__get_document_description()
        self.sim_hash = self.__generate_sim_hash()

        self.last_crawled = datetime.today()

        self.is_relevant = self.__check_relevant()

    def __tokenize_document(self):
        """
        removes stop words, punctuation and stems/lemmatizes all words
        """
        tokens = nltk.tokenize.word_tokenize(self.soup.get_text())
        return tokenize(tokens)

    def __detect_document_language(self):
        return langdetect.detect(' '.join(self.tokens))

    def __get_document_description(self):
        # set site description
        description_tag = self.soup.find('meta', attrs={'name': 'description'})
        if description_tag and 'content' in description_tag.attrs:
            return description_tag['content']
        else:
            return ""

    def __generate_sim_hash(self):
        weights = dict()
        tokens = self.tokens
        for token in tokens:
            if token in weights:
                weights[token] += 1
            else:
                weights[token] = 1

        binary_length = 128
        doc_hashes = [int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16) for token in tokens]
        doc_binaries = [bin(h)[2:].zfill(binary_length) for h in doc_hashes]

        # sum up all columns
        v = [0] * binary_length
        for col in range(binary_length):
            col_sum = 0
            for i, binary in enumerate(doc_binaries):
                w = weights[tokens[i]]
                value = int(binary[col])
                value = -1 if value == 0 else value
                weighted_sum = w * value
                col_sum += weighted_sum
            v[col] = 1 if col_sum > 0 else 0

        # convert list to binary number
        return int("".join(str(x) for x in v), 2)

    @staticmethod
    def __is_external(url: str):
        return url.startswith(('www', 'http', 'https'))

    @staticmethod
    def get_base_url(url: str):
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        return base_url

    def __get_links(self):
        a_tags = self.soup.find_all("a", href=True)
        hrefs = set()

        for a in a_tags:
            href = a.get('href')
            if Document.__is_external(href):
                hrefs.add(href)
            else:
                hrefs.add(Document.get_base_url(self.url) + href)
        return hrefs

    def __getstate__(self):
        state = self.__dict__
        # exclude the soup from the pickle serialisation to reduce file size
        if "soup" in state:
            del state["soup"]

        return state

    def __check_relevant(self):
        for token in self.tokens:
            if token == "Tübingen" or token == "tübingen":
                return True
        return False
