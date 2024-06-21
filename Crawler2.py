import os
import sys
from Document import Document
from queue import Queue
import pickle
from datetime import date


sys.setrecursionlimit(100000)
  
frontier = Queue()
frontier.put("https://uni-tuebingen.de/en/")

# hashes of urls that have already been visited
already_visited = {}

def save_pickle(obj, path):
  with open(path, "wb") as f:
    pickle.dump(obj, f)


def load_pickle(path):
  with open(path, "rb") as f:
    return pickle.load(f)


def crawl():
  while not frontier.empty():
    url = frontier.get()
    url_hash = hash(url)
    if (already_visited.get(url_hash) is None or already_visited.get(url_hash) < date.today()):# and content of webpage has been changed since then! 
      print(url)
      try:
        doc = Document(url)
      except Exception as e:
        print("\t" + str(e))
        already_visited[url_hash] = date.max # unable to crawl
        continue
      already_visited[url_hash] = doc.last_crawl

      for l in doc.links:
        frontier.put(l)

      path = os.path.join(os.getcwd(), "documents", f"{doc.url_hash}.pickle")
      save_pickle(doc, path)
    else:
      print("already visited", url)


if __name__ == '__main__':
    # create folder for documents

    os.chdir("C:/Users/Frauke/Documents/Studium_Master/Semester_4/Modern Search Engines")
    folder_path = os.path.join(os.getcwd(), "documents")
    if not os.path.exists(folder_path):
      os.makedirs(folder_path)

    crawl()