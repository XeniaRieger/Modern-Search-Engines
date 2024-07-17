import collections
import math
import os
import pickle
from datetime import datetime

from Tokenizer import tokenize, tokenize_query


def create_float_defaultdict():
    return collections.defaultdict(float)

def load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)

class BM25Ranker:

    def __init__(self, index, k1=1.5, b=0.75):
        self.__index = index
        self.__bm25_doc_term = collections.defaultdict(create_float_defaultdict)
        self.k1 = k1
        self.b = b
        self.l = 0.5 # lambda parameter for exponential distribution for weighting recent document vs older
        # calculate average date

    def calculate_average_date(self):
        parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
        documents_path = os.path.join(parent_path, "serialization", "documents", "pickle")

        for root, dirs, files in os.walk(documents_path):
            print(len(files))
            for file in files:
                if file.endswith('.pickle'):
                    with open(os.path.join(root, file), 'rb') as f:
                        pickle.load(f)





    def calculate_bm25_doc_term(self):
        for doc_id, terms in self.__index.tf.items():
            doc_len = sum(terms.values())

            doc_date = self.__index.doc_dates[doc_id] if self.__index.doc_dates[doc_id] != 0.0 else self.__index.avg_date
            now = datetime.now().timestamp()
            exponent = -self.l * (now - doc_date)/3600
            time_factor = math.exp(exponent) # lambda zwischen 0 und 1
            time_factor = 1

            breaktg = 0
            for term, tf in terms.items():
                w = self.get_fields_weight(term, doc_id)

                fraction = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * (doc_len / self.__index.avg_doc_length)))
                self.__bm25_doc_term[doc_id][term] = time_factor * w * self.__index.idf[term] * fraction

    def __query_bm25(self, query_tokens):
        query_bm25 = collections.defaultdict(float)
        for term in query_tokens:
            if term in self.__index.inverted_index:
                for doc_id in self.__index.inverted_index[term]:
                    if term in self.__bm25_doc_term[doc_id]:
                        query_bm25[doc_id] += self.__bm25_doc_term[doc_id][term]
        return query_bm25

    def search(self, query: str, top_k: int = 10):
        query_tokens = tokenize_query(query)
        query_bm25 = self.__query_bm25(query_tokens)
        sorted_query_bm25 = sorted(query_bm25.items(), key=lambda item: item[1], reverse=True)
        self.calculate_bm25_doc_term()
        for item in sorted_query_bm25[:top_k]:
            print(self.__index.urls[item[0]])
        return sorted_query_bm25[:top_k]

    def get_fields_weight(self, term, doc_id):
        w = 1
        if term in self.__index.titles[doc_id]:
            w *= 1.5
        if term in self.__index.headings[doc_id]:
            w *= 1.25
        if term in self.__index.bolds[doc_id]:
            w *= 1.1
        if term in self.__index.italics[doc_id]:
            w *= 1.1
        return w


