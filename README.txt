To use the doc2query implementation download the models by running 
pip install --upgrade git+https://github.com/terrierteam/pyterrier_doc2query.git
pip install --upgrade git+https://github.com/terrierteam/pyterrier_dr.git

CHANGES FROM OBJECTORIENTED BRANCH:
1) use visible part of webpage only -> important for doc2query model
2) Read in a starting frontier
3) use doc2query model to expand document before tokenizing it -> bigger run time... Relevance can be calculated cheaper if too much

TO TEST:
1) Confidence value for Relevance Model

