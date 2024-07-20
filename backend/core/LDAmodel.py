import os
import gensim
from gensim.corpora.dictionary import Dictionary
from DocumentIndex import DocumentIndex
from Document import Document
import pickle
from gensim.test.utils import datapath
import collections

class LDAmodel:

	def __init__(self):
		self.document_topics = collections.defaultdict(int)
		self.topics = None

	def train_model(self, train_docs: int = 1000, topic_num: int = 10):
		doc_tokens = []
		doc_ids = []
		parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
		for p in os.listdir(os.path.join(parent_path, "serialization", "documents", "pickle")):
			with open(os.path.join(parent_path, "serialization", "documents", "pickle", p), 'rb') as f:
				doc = pickle.load(f)
				doc_tokens.append(doc.single_tokens)
				doc_ids.append(doc.url_hash)

		common_dictionary  = Dictionary(doc_tokens[:train_docs])
		corpus = [common_dictionary.doc2bow(text) for text in doc_tokens]
		lda = gensim.models.LdaModel(corpus=corpus, num_topics=topic_num, id2word=common_dictionary)

		dictionary = [common_dictionary.doc2bow(text) for text in doc_tokens]
		for i in range(len(doc_ids)):
			self.document_topics[doc_ids[i]] = lda[dictionary[i]]

		self.topics = lda.print_topics()

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

	def load(path):
		with open(path, 'rb') as f:
			return pickle.load(f)

if __name__ == '__main__':
	parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
	model = LDAmodel()
	model.train_model()
	model.save(os.path.join(parent_path, "serialization", "ldamodel.pickle"))
