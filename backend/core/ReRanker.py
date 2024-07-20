from BM25Ranker import BM25Ranker
from DocumentIndex import *
from Document import Document
from LDAmodel import *
import pickle

class ReRanker:

	# parameter relevance_importance controls the importance of relevance scores vs. diversity
	# 0 <= relevance_importance <= 1, higher number favors relevance
	# consider specifies how many documents ranked below the current one are considered for reranking (smaller number = faster)
	def __init__(self, relevance_importance: int = 0.7, consider: int = 50):
		parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
		lda = LDAmodel.load(os.path.join(parent_path, "serialization", "ldamodel.pickle"))
		self.doc_topics = lda.document_topics
		self.topics = lda.topics
		self.topic_names = self.parse_topic_names()
		self.relevance_importance = relevance_importance
		self.consider = consider
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

	def diversify(self, ranking):
		reranked = []
		documents = ranking.copy()
		# add the single most relevant document to our ranking
		reranked.append(ranking[0])
		documents.remove(documents[0])	    
		while documents:
			# greedily add the single document that maximizes the weighted mix of l * relevance + (1-l) diversity up to set amout of docs by consider
			v_max = 0
			max_doc = None
			for doc in documents[:self.consider]:
				reranked.append(doc)
				v = self.relevance_importance * self.measure_relevance(reranked) + (1 - self.relevance_importance) * self.measure_diversity(reranked)
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
		for doc_id in ranking:
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
	def rank_documents(self, query: str, top_k: int = 10, topic_threshhold: int = 0.2):
		parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
		index = DocumentIndex.load(os.path.join(parent_path, "serialization", "index.pickle"))
		self.original_ranking = index.retrieve_bm25(query, top_k)
		if not self.original_ranking:
			return []
		ranking = self.diversify(self.original_ranking)
		for doc in ranking:
			topics = [self.topic_names[t[0]] for t in self.doc_topics[doc["url_hash"]] if t[1] >= topic_threshhold]
			doc['topics'] = topics
		return ranking