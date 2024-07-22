import os
import gensim
from gensim.corpora.dictionary import Dictionary
import pickle
import collections
import random


class LDAmodel:

    def __init__(self):
        self.document_topics = collections.defaultdict(int)
        self.topics = None

    def train_model(self, train_docs: int = 500, topic_num: int = 20):
        doc_tokens = []
        doc_ids = []
        forbidden_words = ["tuebingen", "tübingen"]
        parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
        print("loading documents")
        for p in os.listdir(os.path.join(parent_path, "serialization", "documents", "pickle")):
            with open(os.path.join(parent_path, "serialization", "documents", "pickle", p), 'rb') as f:
                doc = pickle.load(f)
                doc_tokens.append([text for text in doc.single_tokens if text not in forbidden_words])
                doc_ids.append(doc.url_hash)

        print("start training...")
        if train_docs >= len(doc_tokens):
            common_dictionary = Dictionary(doc_tokens)
        else:
            common_dictionary = Dictionary(random.sample(doc_tokens, train_docs))
        corpus = [common_dictionary.doc2bow(text) for text in doc_tokens]
        lda = gensim.models.LdaModel(corpus=corpus, num_topics=topic_num, id2word=common_dictionary)
        print("finished training")

        print("assigning topics")
        dictionary = [common_dictionary.doc2bow(text) for text in doc_tokens]
        for i in range(len(doc_ids)):
            self.document_topics[doc_ids[i]] = lda[dictionary[i]]

        topic_names = {}
        for topic in lda.show_topics(num_topics=topic_num):
            if "research" in topic[1].split('"') or "scholar" in topic[1].split('"') or "university" in topic[1].split('"')  or "model" in topic[1].split('"'):
                topic_names[topic[0]] = "University & Research"
            elif "city" in topic[1].split('"') or "town" in topic[1].split('"') or "castle" in topic[1].split('"'):
                topic_names[topic[0]] = "City & Sights"
            elif "travel" in topic[1].split('"') or "hotel" in topic[1].split('"'):
                topic_names[topic[0]] = "Travel"
            elif "food" in topic[1].split('"'):
                topic_names[topic[0]] = "Food & Drinks"
            elif "review" in topic[1].split('"'):
                topic_names[topic[0]] = "Reviews"
            else:
                topic_names[topic[0]] = None
        self.topics = topic_names
        #print(self.topics)
        #print(lda.show_topics(num_topics=topic_num))

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


if __name__ == '__main__':
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
    model = LDAmodel()
    model.train_model()
    model.save(os.path.join(parent_path, "serialization", "ldamodel.pickle"))
