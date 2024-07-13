import Document
import collections
import math
import os
import pickle
from Tokenizer import tokenize
from Doc2Query import doc_2_query_minus


def hamming_distance(hash1, hash2):
    return bin(hash1 ^ hash2).count('1')


# needed for pickle
def create_int_defaultdict():
    return collections.defaultdict(int)


# needed for pickle
def create_float_defaultdict():
    return collections.defaultdict(float)


def load_index(path):
    with open(path, 'rb') as f:
        return pickle.load(f)


class DocumentIndex:

    def __init__(self):
        self.total_documents = 0
        self.inverted_index = collections.defaultdict(set)

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

    def create_index_for_documents(self, documents_path, ngrams=1, use_doc2query=True):
        for root, dirs, files in os.walk(documents_path):
            for file in files:
                if file.endswith('.pickle'):
                    try:
                        with open(os.path.join(root, file), 'rb') as f:
                            self.add(pickle.load(f), ngrams, use_doc2query)
                    except Exception as e:
                        print(str(e))
                        continue
        self.__calculate_tfidf()
        print("index created.")

    def add(self, doc: Document, ngrams, use_doc2query):
        self.total_documents += 1
        single_tokens = doc.single_tokens

        if use_doc2query:
            single_tokens.extend(doc_2_query_minus(doc))

        if ngrams > 1:
            tokens = tokenize(' '.join(single_tokens), ngrams)
        else:
            tokens = single_tokens

        for token in tokens:
            self.__tf[doc.url][token] += 1

        for token in set(tokens):
            self.__df[token] += 1

            if doc.url not in self.inverted_index[token]:
                self.inverted_index[token].add(doc.url)

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
            if token in self.inverted_index:
                for doc_id in self.inverted_index[token]:
                    scores[doc_id] += query_score * self.__tfidf[doc_id][token]
        return scores

    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    def search(self, query: str, top_k: int = 10):
        print("PROCESSING QUERY: ", query)
        query_tokens = tokenize(query.split())
        query_tfidf = self.__calculate_query_tfidf(query_tokens)
        scores = self.__score_documents(query_tfidf)
        ranked_docs = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return ranked_docs[:top_k]


if __name__ == '__main__':
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
    documents_path = os.path.join(parent_path, "serialization", "documents", "pickle")

    index = DocumentIndex()
    index.create_index_for_documents(documents_path, ngrams=3, use_doc2query=True)

    index.save(os.path.join(parent_path, "serialization", "index.pickle"))

    # load an already created index with:
    # index = load_index(os.path.join(parent_path, "serialization", "index.pickle"))

