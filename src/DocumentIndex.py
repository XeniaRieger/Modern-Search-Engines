import Document
import nltk
from nltk.corpus import words
from nltk.corpus import stopwords

from nltk.stem import WordNetLemmatizer

nltk.download('words')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')

lemmatizer = WordNetLemmatizer()
stopwords = stopwords.words('english')


def hamming_distance(hash1, hash2):
    return bin(hash1 ^ hash2).count('1')


# this function is here because document, query and index have to use the same tokenizer
def tokenize(tokens):
    return [lemmatizer.lemmatize(t).lower() for t in tokens if t.isalnum() and t not in stopwords]


class DocumentIndex:

    def __init__(self):
        self.__documents = {}
        self.vocabulary = tokenize(words.words())

    def add(self, doc: Document):
        index_dict = {
            "url_hash": doc.url_hash,
            "sim_hash": doc.sim_hash,
            "last_crawled": doc.last_crawled
        }
        self.__documents[doc.url] = index_dict

    def has_doc(self, url):
        return url in self.__documents

    def get_doc_index(self, url):
        return self.__documents.get(url, None)

    def has_similar_document(self, to_check: Document, threshold=5):
        for url, doc_idx in self.__documents.items():
            if url != to_check.url and hamming_distance(doc_idx["sim_hash"], to_check.sim_hash) < threshold:
                return True
        return False


