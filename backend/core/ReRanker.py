from LDAmodel import LDAmodel
import pickle
import os

class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if name == 'LDAmodel':
            from backend.core.LDAmodel import LDAmodel
            return LDAmodel
        return super().find_class(module, name)

def load_lda_model(path):
    with open(path, 'rb') as f:
        return CustomUnpickler(f).load()

class ReRanker:

    # parameter relevance_importance controls the importance of relevance scores vs. diversity
    # 0 <= relevance_importance <= 1, higher number favors relevance
    # consider specifies how many documents ranked below the current one are considered for reranking (smaller number = faster)
    def __init__(self):
        lda = load_lda_model(os.path.join(os.path.dirname(os.path.normpath(os.getcwd())), "serialization", "ldamodel.pickle"))
        self.doc_topics = lda.document_topics
        self.topics = lda.topics
        self.topic_names = self.parse_topic_names()
        self.original_ranking = None

    def load(self, path):
        with open(path, 'rb') as f:
            return pickle.load(f)

    def parse_topic_names(self):
        topic_names = {}
        for topic in self.topics:
            # use first word (with highest weight for this topic)
            topic_names[topic[0]] = topic[1].split('"')[1]
        return topic_names

    def diversify(self, ranking, relevance_importance, consider):
        reranked = []
        documents = ranking.copy()
        # add the single most relevant document to our ranking
        reranked.append(ranking[0])
        documents.remove(documents[0])
        while documents:
            # greedily add the single document that maximizes the weighted mix of l * relevance + (1-l) diversity up to set amout of docs by consider
            v_max = 0
            max_doc = None
            for doc in documents[:consider]:
                reranked.append(doc)
                v = relevance_importance * self.measure_relevance(reranked) + (1 - relevance_importance) * self.measure_diversity(reranked)
                if v >= v_max:
                    v_max = v
                    max_doc = doc
                reranked.remove(doc)
            reranked.append(max_doc)
            documents.remove(max_doc)
        return reranked

    # 0 <= relevance <= 1
    def measure_relevance(self, ranking):
        relevance = 0.0
        max_relevance = 0.0
        for doc in self.original_ranking[:len(ranking)]:
            max_relevance += doc["score"]
        for doc in ranking:
            relevance += doc["score"]
        return relevance / max_relevance

    # 0 <= diversity <= 1
    def measure_diversity(self, ranking):
        all_topics = {}
        for doc in ranking:
            topics = self.doc_topics[doc["url_hash"]]
            for topic in topics:
                if topic[0] in all_topics:
                    all_topics[topic] += topic[1] / len(ranking)
                else:
                    all_topics[topic] = topic[1] / len(ranking)
        deviation = 0
        perfect_state = 1 / len(self.topics)
        for topic in all_topics:
            deviation += abs(all_topics[topic] - perfect_state)
        if deviation > 1:
            deviation = 1
        return 1 - deviation

    # topic_threshhold: how much percent of words has to belong to a topic, so that the topic is counted
    # 0 <= topic_threshhold <= 1
    def rank_documents(self, original_ranking, topic_threshhold: float = 0.2, relevance_importance: float = 0.7, consider: int = 50):
        self.original_ranking = original_ranking
        if not self.original_ranking:
            return []
        ranking = self.diversify(self.original_ranking, relevance_importance, consider)
        for doc in ranking:
            topics = [self.topic_names[t[0]] for t in self.doc_topics[doc["url_hash"]] if t[1] >= topic_threshhold]
            doc['topics'] = topics
        return ranking
