import collections
from Tokenizer import tokenize
from DocumentIndex import DocumentIndex
def create_int_defaultdict():
    return collections.defaultdict(int)


# needed for pickle
def create_float_defaultdict():
    return collections.defaultdict(float)

class BM25Ranker:
    def __init__(self, index: DocumentIndex):
        self.index = index
        self.__bm25_doc_term = collections.defaultdict(
            create_float_defaultdict)
        self.__calculate_bm25_doc_term(index)

    def __calculate_bm25_doc_term(self, index):
        k = 1.2
        b = 0.75
        index.calculate_idf()
        for doc_id, terms in self.index.get_tf().items():
            for term, count in terms.items():
                idf = index.get_idf()[term]
                fraction = (count * (k + 1)) / (count + k * (1 - b + b * len(terms) / index.get_avg_doc_length()))
                self.__bm25_doc_term[doc_id][term] = idf * fraction

    def __query_bm25(self, query_tokens):
        query_bm25 = collections.defaultdict(float)
        for doc_id in self.index.get_tf():
            for qi in query_tokens:
                qi_bm25 = self.__bm25_doc_term[doc_id][qi]
                query_bm25[doc_id] += qi_bm25
        return query_bm25

    def searchbm25(self, query: str, top_k: int = 10):
        query_tokens = tokenize(query.split())
        query_bm25 = self.__query_bm25(query_tokens)
        sorted_query_bm25 = sorted(query_bm25.items(), key=lambda item: item[1], reverse=True)
        return sorted_query_bm25
