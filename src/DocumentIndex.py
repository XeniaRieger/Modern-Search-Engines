import Document
import collections
import math

from Tokenizer import tokenize


def hamming_distance(hash1, hash2):
    return bin(hash1 ^ hash2).count('1')


# needed for pickle
def create_int_defaultdict():
    return collections.defaultdict(int)


# needed for pickle
def create_float_defaultdict():
    return collections.defaultdict(float)


class DocumentIndex:

    def __init__(self):
        self.__doc_metadata = {}
        self.__inverted_index = collections.defaultdict(set)
        self.total_documents = 0

        self.__tf = collections.defaultdict(create_int_defaultdict)
        self.__df = collections.defaultdict(int)
        self.__idf = collections.defaultdict(float)
        self.__tfidf = collections.defaultdict(create_float_defaultdict)
        self.__avg_doc_length = 0

    def get_inverted_index(self):
        return self.__inverted_index

    def get_tf(self):
        return self.__tf

    def get_idf(self):
        self.calculate_idf()
        return self.__idf

    def get_df(self):
        return self.__df

    def get_avg_doc_length(self):
        return self.__avg_doc_length

    def add(self, doc: Document):
        self.__doc_metadata[doc.url] = {
            "url_hash": doc.url_hash, # in case we need to read the file from disk
            "sim_hash": doc.sim_hash,
            "last_crawled": doc.last_crawled,
            "description": doc.description
        }
        self.total_documents += 1

        for token in doc.tokens:
            self.__tf[doc.url][token] += 1
        for token in set(doc.tokens):
            self.__df[token] += 1

            if doc.url not in self.__inverted_index[token]:
                self.__inverted_index[token].add(doc.url)

        # running average of document length
        self.__avg_doc_length = (self.__avg_doc_length * (self.total_documents - 1) + len(
            doc.tokens)) / self.total_documents

    def calculate_idf(self):
        for term, count in self.__df.items():
            self.__idf[term] = math.log(self.total_documents / count)

    def __calculate_tfidf(self):
        self.calculate_idf()
        for doc_id, terms in self.__tf.items():
            for term, count in terms.items():
                self.__tfidf[doc_id][term] = count * self.__idf[term]

    def has_doc(self, url):
        return url in self.__doc_metadata

    def get_doc_index(self, url):
        return self.__doc_metadata.get(url, None)

    def has_similar_document(self, to_check: Document, threshold=5):
        for url, doc_idx in self.__doc_metadata.items():
            if url != to_check.url and hamming_distance(doc_idx["sim_hash"], to_check.sim_hash) < threshold:
                return True
        return False

    def __calculate_query_tfidf(self, query_tokens):
        query_tf = collections.defaultdict(int)
        for token in query_tokens:
            query_tf[token] += 1

        query_tfidf = collections.defaultdict(float)
        for token, count in query_tf.items():
            if token in self.__idf:
                query_tfidf[token] = count * self.__idf[token]
        return query_tfidf

    def __score_documents(self, query_tfidf):
        scores = collections.defaultdict(float)
        for token, query_score in query_tfidf.items():
            if token in self.__inverted_index:
                for doc_id in self.__inverted_index[token]:
                    scores[doc_id] += query_score * self.__tfidf[doc_id][token]
        return scores

    def search(self, query: str, top_k: int = 10):
        print("PROCESSING QUERY:", query)
        self.__calculate_tfidf() # probably not a good idea to do this for every query
        query_tokens = tokenize(query.split())
        query_tfidf = self.__calculate_query_tfidf(query_tokens)
        scores = self.__score_documents(query_tfidf)
        ranked_docs = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return ranked_docs[:top_k]

