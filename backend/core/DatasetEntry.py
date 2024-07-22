import pickle
import os

class DatasetEntry():
    def __init__(self, name:str, query:str, results:dict, ranking:list[int], engines:list[str]) -> None:
        self.query = query
        self.results = results 
        self.ranking = ranking
        self.name = name
        self.engines = engines
        self.number_ranked = 1
        self.relevant_results = self.get_relevant_results()

    def save(self, path):
        path = os.path.join(path, str(self.name +".pickle"))
        with open(path, 'wb') as f:
            pickle.dump(self, f)
        print("done save!")

    def rerank(self, ranking:list[int]):
        self.number_ranked += 1
        for i in range(len(ranking)):
            self.ranking[i] = self.ranking[i] + ranking[i]
        self.relevant_results = self.get_relevant_results()
    
    def get_relevant_results(self):
        relevant = []
        for i in range(len(self.results)):
            if self.ranking[i] > 0:
                relevant.append(self.results[i].get("url"))
        return relevant

    def print_out(self):
        print(f"name:{self.name}")
        print(f"query: {self.query}")
        print(f"results: \n {self.results}")
        print(f"ranking {self.ranking}")
        print(f"number ranked {self.number_ranked}")
        print(f"relevant results only {self.relevant_results}")