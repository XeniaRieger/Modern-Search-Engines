import os
import sys
from Document import Document
from queue import Queue
import pickle

sys.setrecursionlimit(100000)

frontier = Queue()
frontier.put("https://uni-tuebingen.de/en/")


def save_pickle(obj, path):
  with open(path, "wb") as f:
    pickle.dump(obj, f)


def load_pickle(path):
  with open(path, "rb") as f:
    return pickle.load(f)


def crawl():
  while not frontier.empty():
    url = frontier.get()
    print(url)
    try:
      doc = Document(url)
    except Exception as e:
      print("\t" + str(e))
      continue

    for l in doc.links:
      frontier.put(l)

    path = os.path.join(os.getcwd(), "documents", f"{doc.url_hash}.pickle")
    save_pickle(doc, path)


if __name__ == '__main__':
    # create folder for documents
    folder_path = os.path.join(os.getcwd(), "documents")
    if not os.path.exists(folder_path):
      os.makedirs(folder_path)

    crawl()