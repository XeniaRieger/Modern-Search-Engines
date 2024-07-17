import collections
import os
import pickle

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
            for term, tf in terms.items():
                w = 1
                if term in self.__index.titles[doc_id]:
                    w += 1
                if term in self.__index.headings[doc_id]:
                    w += 0.5
                # add bold, italics
                # time_weight = math.exp(-lambda * (now - doc_date))  lambda am besten kleine werte wie 0.01
                # doc_date is avg date if NONE

                fraction = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * (doc_len / self.__index.avg_doc_length)))
                self.__bm25_doc_term[doc_id][term] = time_weight * w * self.__index.idf[term] * fraction

    def __query_bm25(self, query_tokens):
        query_bm25 = collections.defaultdict(float)
        for term in query_tokens:
            if term in self.__index.inverted_index:
                for doc_id in self.__index.inverted_index[term]:
                    if term in self.__bm25_doc_term[doc_id]:
                        query_bm25[doc_id] += self.__bm25_doc_term[doc_id][term]
        return query_bm25

    def search(self, query_tokens, top_k: int = 10):
        query_bm25 = self.__query_bm25(query_tokens)
        sorted_query_bm25 = sorted(query_bm25.items(), key=lambda item: item[1], reverse=True)
        self.calculate_bm25_doc_term()
        for item in sorted_query_bm25[:top_k]:
            print(self.__index.urls[item[0]])
        return sorted_query_bm25[:top_k]


