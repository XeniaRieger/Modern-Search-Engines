import collections
from BM25Ranker import BM25Ranker
import gensim
from gensim.corpora.dictionary import Dictionary
from DocumentIndex import *
from Document import Document
from gensim.test.utils import datapath
import os
from LDAmodel import *
import pickle

class ReRanker:

	# parameter relevance_importance controls the importance of relevance scores vs. diversity
	# 0 <= relevance_importance <= 1, higher number favors relevance
	# consider specifies how many documents ranked below the current one are considered for reranking (smaller number = faster)
	def __init__(self, relevance_importance: int = 0.7, consider: int = 20):
		parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
		lda = LDAmodel.load(os.path.join(parent_path, "serialization", "ldamodel.pickle"))
		self.doc_topics = lda.document_topics
		self.topics = lda.topics
		self.relevance_importance = relevance_importance
		self.consider = consider
		self.original_ranking = None

	def load(self, path):
		with open(path, 'rb') as f:
			return pickle.load(f)

	def diversify(self, ranking, top_k):
		reranked = []
		documents = ranking.copy()
		# add the single most relevant document to our ranking
		reranked.append(ranking[0])
		documents.remove(documents[0])	    
		while len(reranked) < top_k:
			# greedily add the single document that maximizes the weighted mix of l * relevance + (1-l) diversity up to set amout of docs by consider
			v_max = 0
			max_doc = 0
			for doc in documents[:consider]:
				reranked.append(doc)
				v = self.relevance_importance * measure_relevance(reranked) + (1 - self.relevance_importance) * measure_diversity(reranked)
				if v >= v_max:
					v_max = v
					max_doc = doc
				reranked.remove(doc)
			reranked.append(max_doc)
			documents.remove(max_doc)	        
		return reranked

	# 0 <= relevance <= 1
	def meaure_relevance(self, ranking):
		relevance = 0.0
		max_relevance = 0.0
		for doc_id in self.original_ranking[:len(ranking)]:
			max_relevance += ranking[doc_id]
		for doc_id in ranking:
			relevance += ranking[doc_id]
		return relevance / max_relevance

	# 0 <= diversity <= 1
	def measure_diversity(self, ranking):
		diversity = 0.0
		for doc in ranking:
			print(self.doc_topics[doc.url_hash])

	def rank_documents(self, query: str, top_k: int = 10):
		parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
		index = DocumentIndex.load(os.path.join(parent_path, "serialization", "index.pickle"))
		self.original_ranking = index.retrieve(query, top_k) # TODO change to bm25
		self.measure_diversity(self.original_ranking)

if __name__ == '__main__':
	ranker = ReRanker()
	ranking = ranker.rank_documents("tübingen", 10)