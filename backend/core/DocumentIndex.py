import Document
import collections
import math
import os
import pickle
import datetime
from Tokenizer import tokenize
from Tokenizer import tokenize_query
from Doc2Query import doc_2_query_minus
from BM25Ranker import BM25Ranker
from datetime import *
from tqdm import tqdm

def hamming_distance(hash1, hash2):
    return bin(hash1 ^ hash2).count('1')

# needed for pickle
def create_int_defaultdict():
    return collections.defaultdict(int)

def create_float_defaultdict():
    return collections.defaultdict(float)

def create_list_defaultdict():
    return collections.defaultdict(list)


class DocumentIndex:

    def __init__(self):
        self.inverted_index = collections.defaultdict(set)
        self.total_documents = 0
        self.avg_doc_length = 0
        self.avg_doc_date = None

        # stores, headings, text_emphasis words, and the document date
        self.doc_metadata = {}

        self.tf = collections.defaultdict(create_int_defaultdict)
        self.df = collections.defaultdict(int)
        self.idf = collections.defaultdict(float)
        self.tfidf = collections.defaultdict(create_float_defaultdict)

        self.__bm25_ranker = BM25Ranker(self)

    def create_index_for_documents(self, documents_path, ngrams=1, use_doc2query=True):
        print("loading documents...")
        docs = self.__load_documents(documents_path)

        print("Calculating averages...")
        self.__calculate_averages(docs)

        print(f"Average Document Length: {self.avg_doc_length}")
        print(f"Average Document Date: {self.avg_doc_date}")

        self.total_documents = len(docs)

        if use_doc2query:
            print("Calculating doc2query (takes long)")
            doc_2_query_minus(docs, ngrams)

        print("Indexing documents...")
        for doc in tqdm(docs):
            self.__add(doc, ngrams)

        print("Calculating TF-IDF scores...")
        self.__calculate_tfidf()

        print("BM25 calculations...")
        self.__bm25_ranker.calculate_bm25_doc_term()

        print("Index created.")

    def __load_documents(self, documents_path):
        docs = []
        for root, dirs, files in os.walk(documents_path):
            for file in tqdm(files):
                if file.endswith('.pickle'):
                    try:
                        with open(os.path.join(root, file), 'rb') as f:
                            doc = pickle.load(f)
                            if doc.is_relevant:
                                docs.append(doc)
                    except Exception as e:
                        print(str(e))
                        continue
        return docs

    def __calculate_averages(self, docs):
        # calculate average date, length
        total_date_timestamp = 0
        total_docs_with_date = 0
        doc_len_counter = 0

        for doc in tqdm(docs):
            doc_len_counter += len(doc.single_tokens)
            if hasattr(doc, "last_modified") and doc.last_modified:
                total_date_timestamp += doc.last_modified.timestamp()
                total_docs_with_date += 1

        if total_docs_with_date > 0:
            self.avg_doc_date = datetime.fromtimestamp((total_date_timestamp / total_docs_with_date))

        self.avg_doc_length = doc_len_counter / len(docs)

    def __add(self, doc: Document, ngrams):
        single_tokens = doc.single_tokens

        self.doc_metadata[doc.url_hash] = {}
        self.doc_metadata[doc.url_hash]['date'] = doc.last_modified if doc.last_modified is not None else self.avg_doc_date
        self.doc_metadata[doc.url_hash]['headings'] = {}
        self.doc_metadata[doc.url_hash]['text_emphasis'] = {}

        # TODO check if this is useful or not
        # extend the tokens by the description meta information
        # if doc.description is not None:
        #     single_tokens.extend(tokenize(doc.description))

        tokens = tokenize(' '.join(single_tokens), ngrams) if ngrams > 1 else single_tokens
        if doc.title:
            title_tokens = tokenize(doc.title, ngrams)
            self.doc_metadata[doc.url_hash]['title'] = title_tokens
            tokens.extend(title_tokens)

        for token in tokens:
            self.tf[doc.url_hash][token] += 1

        for token in set(tokens):
            self.df[token] += 1
            self.inverted_index[token].add(doc.url_hash)

        for tag, headings in doc.headings.items():
            self.doc_metadata[doc.url_hash]['headings'][tag] = set([])
            for h in headings:
                self.doc_metadata[doc.url_hash]['headings'][tag].update(tokenize(h, ngrams))

        for tag, emphasis in doc.text_emphasis.items():
            self.doc_metadata[doc.url_hash]['text_emphasis'][tag] = set([])
            for d in emphasis:
                self.doc_metadata[doc.url_hash]['text_emphasis'][tag].update(tokenize(d, ngrams))

    def __calculate_idf(self):
        for term, count in self.df.items():
            self.idf[term] = math.log(self.total_documents / count)

    def __calculate_tfidf(self):
        self.__calculate_idf()
        for doc_id, terms in tqdm(self.tf.items()):
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

    def __getstate__(self):
        state = self.__dict__
        del state["doc_metadata"]
        return state

    @staticmethod
    def load(path):
        with open(path, 'rb') as f:
            loaded = pickle.load(f)
            new_index = DocumentIndex()
            new_index.__dict__.update(loaded.__dict__)
            return new_index

    def __sort_scores(self, scores):
        return sorted(scores.items(), key=lambda item: item[1], reverse=True)

    def __get_documents(self, doc_ids):
        parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
        documents_path = os.path.join(parent_path, "serialization", "documents", "pickle")
        docs = []
        for (doc_id, score) in doc_ids:
            with open(os.path.join(documents_path, doc_id+".pickle"), 'rb') as f:
                doc = pickle.load(f)
                docs.append({
                    "url": doc.url,
                    "url_hash": doc.url_hash,
                    "title": doc.title,
                    "description": doc.description,
                    "icon_url": doc.icon_url,
                    "score": score,
                    "raw_text": doc.raw_text,
                })
        return docs

    def retrieve_tfidf(self, query: str, top_k: int = 10):
        query_tokens = tokenize_query(query)
        query_tfidf = self.__calculate_query_tfidf(query_tokens)
        scores = self.__score_documents(query_tfidf)
        sorted = self.__sort_scores(scores)
        return self.__get_documents(sorted[:top_k])

    def retrieve_bm25(self, query, top_k: int = 10):
        query_tokens = tokenize_query(query)
        scores = self.__bm25_ranker.query_bm25(query_tokens)
        sorted = self.__sort_scores(scores)
        return self.__get_documents(sorted[:top_k])


if __name__ == '__main__':
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
    documents_path = os.path.join(parent_path, "serialization", "documents", "pickle")

    index = DocumentIndex()
    index.create_index_for_documents(documents_path, ngrams=3, use_doc2query=True)

    index.save(os.path.join(parent_path, "serialization", "index.pickle"))
    #
    # load an already created index with:
    # index = DocumentIndex.load(os.path.join(parent_path, "serialization", "index.pickle"))
    # print(index.retrieve_bm25("Hotels"))
