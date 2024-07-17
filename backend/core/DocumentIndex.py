import Document
import collections
import math
import os
import pickle
from Tokenizer import tokenize
from Doc2Query import doc_2_query_minus
from BM25Ranker import BM25Ranker

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
        self.total_documents = 0
        self.avg_doc_length = 0

        self.inverted_index = collections.defaultdict(set)
        self.urls = collections.defaultdict(str)
        self.tf = collections.defaultdict(create_int_defaultdict)
        self.titles = collections.defaultdict(list)
        self.df = collections.defaultdict(int)
        self.idf = collections.defaultdict(float)
        self.tfidf = collections.defaultdict(create_float_defaultdict)
        self.headings = collections.defaultdict(list)

        self.__bm25_ranker = BM25Ranker(self)

    def create_index_for_documents(self, documents_path, ngrams=1, use_doc2query=True):
        for root, dirs, files in os.walk(documents_path):
            for file in files:
                if file.endswith('.pickle'):
                    try:
                        with open(os.path.join(root, file), 'rb') as f:
                            doc = pickle.load(f)
                            if doc.is_relevant:
                                self.add(doc, ngrams, use_doc2query)
                    except Exception as e:
                        print(str(e))
                        continue
        self.__calculate_tfidf()
        self.__bm25_ranker.calculate_bm25_doc_term()
        print("index created.")

    def add(self, doc: Document, ngrams, use_doc2query):
        self.total_documents += 1
        single_tokens = doc.single_tokens

        if use_doc2query:
            single_tokens.extend(doc_2_query_minus(doc))

        # TODO check if this is useful or not
        # extend the tokens by the description meta information
        # if doc.description is not None:
        #     single_tokens.extend(tokenize(doc.description))

        if ngrams > 1:
            tokens = tokenize(' '.join(single_tokens), ngrams)
        else:
            tokens = single_tokens

        for token in tokens:
            self.tf[doc.url_hash][token] += 1

        for token in set(tokens):
            self.df[token] += 1
            self.inverted_index[token].add(doc.url_hash)

        if doc.title is not None:
            self.titles[doc.url_hash] = doc.title

        if doc.headings is not None:
            self.headings[doc.url_hash] = doc.headings

        self.urls[doc.url_hash] = doc.url


        # update average of document length
        self.avg_doc_length = (self.avg_doc_length * (self.total_documents - 1) + len(tokens)) / self.total_documents

        print(f"added {doc.url}")

    def __calculate_idf(self):
        for term, count in self.df.items():
            self.idf[term] = math.log(self.total_documents / count)

    def __calculate_tfidf(self):
        self.__calculate_idf()
        for doc_id, terms in self.tf.items():
            for term, count in terms.items():
                self.tfidf[doc_id][term] = count * self.idf[term]

    def __calculate_query_tfidf(self, query_tokens):
        query_tf = collections.defaultdict(int)
        for token in query_tokens:
            query_tf[token] += 1

        query_tfidf = collections.defaultdict(float)
        for token, count in query_tf.items():
            if token in self.idf:
                query_tfidf[token] = count * self.idf[token]
        return query_tfidf

    def __score_documents(self, query_tfidf):
        scores = collections.defaultdict(float)
        for token, query_score in query_tfidf.items():
            if token in self.inverted_index:
                for doc_id in self.inverted_index[token]:
                    scores[doc_id] += query_score * self.tfidf[doc_id][token]
        return scores

    def save(self, path):
        tmp_path = path + ".tmp"
        with open(tmp_path, 'wb') as f:
            pickle.dump(self, f)

        renamed = False
        while not renamed:
            try:
                os.replace(tmp_path, path)
                renamed = True
            except PermissionError:
                continue

    @staticmethod
    def load(path):
        with open(path, 'rb') as f:
            return pickle.load(f)

    def retrieve(self, query: str, top_k: int = 10):
        query_tokens = tokenize_query(query)
        query_tfidf = self.__calculate_query_tfidf(query_tokens)
        scores = self.__score_documents(query_tfidf)
        ranked_docs = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return self.__get_documents(ranked_docs[:top_k])

    def retrieve_bm25(self, query, top_k: int = 10):
        doc_ids = self.__bm25_ranker.search(query, top_k)
        return self.__get_documents(doc_ids)

    def __get_documents(self, doc_ids):
        parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
        documents_path = os.path.join(parent_path, "serialization", "documents", "pickle")
        docs = []
        for (doc_id, score) in doc_ids:
            with open(os.path.join(documents_path, doc_id+".pickle"), 'rb') as f:
                doc = pickle.load(f)
                docs.append({
                    "url": doc.url,
                    "title": doc.title,
                    "description": doc.description,
                    "icon_url": doc.icon_url,
                    "score": score
                })
        return docs


if __name__ == '__main__':
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
    documents_path = os.path.join(parent_path, "serialization", "documents", "pickle")

    index = DocumentIndex()
    index.create_index_for_documents(documents_path, ngrams=1, use_doc2query=True)

    index.save(os.path.join(parent_path, "serialization", "index.pickle"))

    # load an already created index with:
    # index = DocumentIndex.load(os.path.join(parent_path, "serialization", "index.pickle"))

