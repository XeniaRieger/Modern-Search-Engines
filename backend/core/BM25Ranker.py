import collections
import pickle

from Tokenizer import tokenize


def create_float_defaultdict():
    return collections.defaultdict(float)


class BM25Ranker:

    def __init__(self, index, k=1.5, b=0.75):
        self.__index = index
        self.__bm25_doc_term = collections.defaultdict(create_float_defaultdict)
        self.k = k
        self.b = b
        self.calculate_bm25_doc_term()

    def calculate_bm25_doc_term(self):
        for doc_id, terms in self.__index.tf.items():
            for term, tf in terms.items():
                w = 1
                if term in self.__index.titles[doc_id]:
                    w += 0.25
                if term in self.__index.headings[doc_id]:
                    w += 0.25

                fraction = (tf * (self.k + 1)) / (tf + self.k * (1 - self.b + self.b * (len(terms) / self.__index.avg_doc_length)))
                self.__bm25_doc_term[doc_id][term] = w * self.__index.idf[term] * fraction

    def __query_bm25(self, query_tokens):
        query_bm25 = collections.defaultdict(float)
        for doc_id in self.__index.tf:
            for qi in query_tokens:
                query_bm25[doc_id] += self.__bm25_doc_term[doc_id][qi]
        return query_bm25

    def search(self, query: str, top_k: int = 10):
        query_tokens = tokenize(query)
        query_bm25 = self.__query_bm25(query_tokens)
        sorted_query_bm25 = sorted(query_bm25.items(), key=lambda item: item[1], reverse=True)
        self.calculate_bm25_doc_term()
        for item in sorted_query_bm25[:top_k]:
            print(self.__index.urls[item[0]])
        return sorted_query_bm25[:top_k]


