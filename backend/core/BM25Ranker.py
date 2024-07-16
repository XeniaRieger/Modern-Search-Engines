import collections
from Tokenizer import tokenize


def create_float_defaultdict():
    return collections.defaultdict(float)


class BM25Ranker:

    def __init__(self, index, k1=1.5, b=0.75):
        self.__index = index
        self.__bm25_doc_term = collections.defaultdict(create_float_defaultdict)
        self.k1 = k1
        self.b = b

    def calculate_bm25_doc_term(self):
        for doc_id, terms in self.__index.tf.items():
            doc_len = sum(terms.values())
            for term, tf in terms.items():
                fraction = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * (doc_len / self.__index.avg_doc_length)))
                self.__bm25_doc_term[doc_id][term] = self.__index.idf[term] * fraction

    def __query_bm25(self, query_tokens):
        query_bm25 = collections.defaultdict(float)
        for term in query_tokens:
            if term in self.__index.inverted_index:
                for doc_id in self.__index.inverted_index[term]:
                    if term in self.__bm25_doc_term[doc_id]:
                        query_bm25[doc_id] += self.__bm25_doc_term[doc_id][term]
        return query_bm25

    def search(self, query: str, top_k: int = 10):
        query_tokens = tokenize(query)
        query_bm25 = self.__query_bm25(query_tokens)
        sorted_query_bm25 = sorted(query_bm25.items(), key=lambda item: item[1], reverse=True)
        return sorted_query_bm25[:top_k]
