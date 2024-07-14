To use the doc2query implementation download the models by running 
pip install --upgrade git+https://github.com/terrierteam/pyterrier_doc2query.git
pip install --upgrade git+https://github.com/terrierteam/pyterrier_dr.git

# General
- First the crawler runs and saves the documents on disk as pickle files.
The crawler is designed to respect the robots.txt file and crawl delays
- When the crawler is finished, the index is built. It reads the documents from disk,
 stores them inside an inverted index and calculates the TF-IDF. By default, it extends the
 document tokens by the doc2query method.

# Run Crawler
To run the crawler execute ``python .\backend\core\Crawler.py``.
The crawled documents are stored as pickle files inside ``serialization\documents``.
The state of the crawler is also stored in this folder as ``crawl_state.pickle``.

# Run Index
To index all documents execute ``python .\backend\core\DocumentIndex.py``. The generated index file
is stored at ``serialization\documents\index.pickle``.

# Run REST API Server
To start the django rest server:
```
cd backend\SearchEngineServer
python manage.py runserver
```
this will automatically load the index inside the serialization folder.
The server will listen on port 8000 to answer query requests.

# Run React frontend
```
cd frontend
npm start
```

