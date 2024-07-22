
## General
- First the crawler runs and saves the documents on disk as pickle files.
The crawler is designed to respect the robots.txt file and crawl delays
- When the crawler is finished, the index is built. It reads the documents from disk,
 stores them inside an inverted index and calculates the TF-IDF. By default, it extends the
 document tokens by the doc2query method.

## Install requirements
```
cd backend
pip install -r requirements.txt
```
To use the doc2query implementation download the models by running
```
pip install --upgrade git+https://github.com/terrierteam/pyterrier_doc2query.git
pip install --upgrade git+https://github.com/terrierteam/pyterrier_dr.git
```


## Run Crawler
To run the crawler execute 
```
cd backend/core
python Crawler.py
```
The crawled documents are stored as pickle files inside ``serialization\documents``.
The state of the crawler is also stored in this folder as ``crawl_state.pickle``. When a crawl_state file already exists,
the crawler will load the file and resume the crawling from the loaded frontier.

## Run Index
To index all documents execute 
```
cd backend/core
python DocumentIndex.py
```
The generated index file is stored at ``serialization\documents\index.pickle``.

## Run Topic Model
The topic model is needed to rerank documents for diversity. A model trained on already crawled documents is stored at``serialization\ldamodel.pickle``. 
To train a new model on your crawled documents execute:
```
cd backend/core
python LDAmodel.py
```

## Run REST API Server
To start the django rest server:
```
cd backend/SearchEngineServer
python manage.py runserver
```
This will automatically load the index inside the serialization folder.
The server will listen on port 8000 to answer query requests.

## Run React frontend
Starts the frontend on port 3000
```
cd frontend
npm install
npm start
```

## Run batch retrieval
```
cd backend/core
python batch_retrieve.py path/to/queryFile.txt path/to/resultList.txt
```
The query file should contain one query number and one query per line seperated by tabs.

## Run Evalation GUI
```
cd backend/core
python streamlit run DatasetCreator.py
```
