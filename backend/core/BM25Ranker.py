import collections
import math
from datetime import datetime, timezone
from tqdm import tqdm

def create_float_defaultdict():
    return collections.defaultdict(float)

class BM25Ranker:

    def __init__(self, index, k1=1.5, b=0.75):
        self.__index = index
        self.__bm25_doc_term = collections.defaultdict(create_float_defaultdict)
        self.__k1 = k1
        self.__b = b
        self.__lambda = 0.008  # exponential distribution for weighting recent document vs older

    def calculate_bm25_doc_term(self):
        now = datetime.now(timezone.utc)
        for doc_id, terms in tqdm(self.__index.tf.items()):
            doc_len = sum(terms.values())
            time_weight = self.__get_recency_score(doc_id, now)
            for term, tf in terms.items():
                weight = self.__get_weight(term, doc_id)
                fraction = (tf * (self.__k1 + 1)) / (tf + self.__k1 * (1 - self.__b + self.__b * (doc_len / self.__index.avg_doc_length)))
                self.__bm25_doc_term[doc_id][term] = time_weight * weight * self.__index.idf[term] * fraction

    def __get_weight(self, term, doc_id):
        w = 1.0
        doc = self.__index.doc_metadata[doc_id]
        if 'title' in doc and term in doc['title']:
            w *= 1.75

        for h in doc['headings'].values():
            if term in h:
                w *= 1.5

        for e in doc['text_emphasis'].values():
            if term in e:
                w *= 1.1

        return w

    def __get_recency_score(self, doc_id, now):
        doc_date = self.__index.doc_metadata[doc_id]['date']
        age = (now - doc_date.astimezone()).days
        return math.exp(-self.__lambda * age)

    def query_bm25(self, query_tokens):
        query_bm25 = collections.defaultdict(float)
        for term in query_tokens:
            if term in self.__index.inverted_index:
                for doc_id in self.__index.inverted_index[term]:
                    if term in self.__bm25_doc_term[doc_id]:
                        query_bm25[doc_id] += self.__bm25_doc_term[doc_id][term]
        return query_bm25


