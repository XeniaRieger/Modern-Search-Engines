from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin
import hashlib
import langdetect
from langdetect.lang_detect_exception import LangDetectException
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from datetime import datetime
from Tokenizer import tokenize

langdetect.DetectorFactory.seed = 123


class Document:

    def __init__(self, url: str, save_html_file_extra=False):
        self.url = url
        self.url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        self.soup = None
        self.sim_hash = None
        self.language = None
        self.description = None
        self.single_tokens = None  # single word tokens  no n-grams!
        self.raw_text = None       # the raw document text with stopwords etc
        self.raw_html = None
        self.title = None
        self.headings = []
        self.links = []
        self.last_crawled = None
        self.is_relevant = None
        self.save_html_file_extra = save_html_file_extra

        # fetch document content and store the relevant information
        self.__fetch_document_content()


    def __check_if_url_is_html(self, url, headers):
        try:
            res = requests.get(url, timeout=5, headers=headers, stream=True)
            content_type = res.headers.get('Content-Type', '')
            print(content_type, end="\t")

            if 'text/html' not in content_type:
                return False

            # some sites claim to be text/html but are pdf thus we look into the first bytes
            initial_bytes = res.raw.read(512)
            if initial_bytes[:4] == b'%PDF':
                return False

            return True
        except:
            return False

    def __fetch_document_content(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        if not self.__check_if_url_is_html(self.url, headers):
            raise Exception("Not HTML page")

        res = requests.get(self.url, timeout=5, headers=headers)

        if res.status_code != 200:
            raise Exception("Request failed with status: " + str(res.status_code))

        self.raw_html = res.text
        self.soup = BeautifulSoup(res.text, 'html.parser')
        self.description = self.__get_document_description()

        # remove unnecessary elements
        for tag in self.soup(["script", "style", "link", "meta"]):
            tag.decompose()

        self.extract_fields()


        text = self.soup.find("main")
        if not text:
            text = self.soup.get_text()
        else:
            text = " ".join(text.stripped_strings)

        self.raw_text = text
        self.single_tokens = tokenize(text, ngrams=1)

        # TODO check if this is useful or not
        # extend the tokens by the description meta information
        # if self.description is not None:
        #     self.tokens.extend(tokenize(self.description))

        self.language = self.__detect_document_language()
        self.links = self.__get_links()
        self.sim_hash = self.__generate_sim_hash()
        self.last_crawled = datetime.today()
        self.is_relevant = self.__check_relevant()

    def __detect_document_language(self):
        try:
            # first extract the lang property from the html tag
            # we add 25% probability to the language thats listed in the html tag
            # then detect the language of the text content
            # if the "en" language is above 50%, the document is considered english

            html_tag = self.soup.find('html')
            html_lang = None
            if hasattr(html_tag, 'attrs'):
                html_lang = html_tag.attrs.get('lang', None)
                if html_lang is not None:
                    html_lang = html_lang.split('-')[0] # converts en-LS or en-GB to en

            detected_langs = {lang.lang: lang.prob for lang in langdetect.detect_langs(' '.join(self.single_tokens))}
            if html_lang is not None and html_lang in detected_langs:
                detected_langs[html_lang] += 0.25

            sorted_langs = dict(sorted(detected_langs.items(), key=lambda item: item[1], reverse=True))
            if 'en' in sorted_langs and sorted_langs['en'] > 0.5:
                return 'en'

            # if the document is not english we just return the highest prob language
            return list(sorted_langs.keys())[0]
        except LangDetectException:
            return None
    
    def __get_document_description(self):
        description_tag = self.soup.find('meta', attrs={'name': 'description'})
        if description_tag and 'content' in description_tag.attrs:
            return description_tag['content']

        # Check for 'og:description' meta tag if 'description' not found
        og_description_tag = self.soup.find('meta', attrs={'property': 'og:description'})
        if og_description_tag and 'content' in og_description_tag.attrs:
            return og_description_tag['content']

        return ""

    def __generate_sim_hash(self, hash_len=128):
        weights = dict()
        tokens = self.single_tokens
        for token in tokens:
            if token in weights:
                weights[token] += 1
            else:
                weights[token] = 1

        doc_hashes = [int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16) for token in tokens]
        doc_binaries = [bin(h)[2:].zfill(hash_len) for h in doc_hashes]

        # sum up all columns
        v = [0] * hash_len
        for col in range(hash_len):
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

    @staticmethod
    def get_domain(url: str):
        domain = urlparse(url).netloc
        domain = domain.replace("www.", "")
        return domain

    @staticmethod
    def __is_valid_url(url):
        validate_url = URLValidator()
        try:
            validate_url(url)
        except ValidationError as e:
            return False
        return True

    def __get_links(self):
        a_tags = self.soup.find_all("a", href=True)
        hrefs = set()

        for a in a_tags:
            href = a.get('href')
            if Document.__is_external(href) and Document.__is_valid_url(href):
                hrefs.add(href)
            else:
                url = urljoin(Document.get_base_url(self.url), href)
                if Document.__is_valid_url(url):
                    hrefs.add(url)
        return hrefs

    def __getstate__(self):
        state = self.__dict__
        # exclude the soup from the pickle serialisation to reduce file size
        if "soup" in state:
            del state["soup"]

        if not self.save_html_file_extra and "raw_html" in state:
            del state["raw_html"]

        del state["save_html_file_extra"]
        return state

    def __check_relevant(self):
        words = ["tübingen", "tuebingen", "tubingen"]

        if self.language is None or self.language != "en":
            return False

        url_lower = self.url.lower()
        if any(w in url_lower for w in words):
            return True

        for token in self.single_tokens:
            if token in words:
                return True
        return False

    '''
    extracts the tokens in html tags 'title' and headings and stores them in self.title and self.headings
    '''
    def extract_fields(self):
        if self.soup.find("title") is not None:
            self.title = tokenize(self.soup.find("title").text,ngrams=1)

        headings = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for heading in headings:
            self.headings.extend(tokenize(heading.text, ngrams = 1))



