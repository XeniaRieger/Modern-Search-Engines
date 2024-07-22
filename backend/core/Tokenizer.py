import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from spellchecker import SpellChecker

nltk.download('words')
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')

spell = SpellChecker()

lemmatizer = WordNetLemmatizer()
stopwords = stopwords.words('english')


def tokenize(text: str, ngrams=3) -> list:
    text = text.lower().replace("tuebingen", "tübingen").replace("tubingen", "tübingen").replace("tübinger", "tübingen")
    tokens = nltk.tokenize.word_tokenize(text)
    cleaned_tokens = [lemmatizer.lemmatize(t) for t in tokens if t.isalnum() and t not in stopwords]


    ngram_list = []
    for n in range(1, ngrams + 1):
        ngram_list.extend([" ".join(t) for t in nltk.ngrams(cleaned_tokens, n)])

    return ngram_list

def tokenize_query(query: str, ngrams=3, max_length_before_ngram=40):
    max_length = max_length_before_ngram
    query = query.lower()
    tokens = nltk.tokenize.word_tokenize(query)
    # correct misspelled words
    tokens = [spell.correction(t) for t in tokens if spell.correction(t) is not None]
    # try to remove Tübingen because every doc is about tübingen
    try_query = [e for e in tokens if e not in ("tuebingen", "tubingen", "tübingen", "tübinger")]
    if not try_query:
        query = tokens
    else:
        query = try_query
    # try to remove stopwords + lemmatize
    cleaned_tokens = [lemmatizer.lemmatize(t) for t in query if t.isalnum() and t not in stopwords]
    if cleaned_tokens:
        query = cleaned_tokens
    else:
        min_clean = [lemmatizer.lemmatize(t) for t in query if t.isalnum()]
        if min_clean:
            query = min_clean
        else:
            query = [lemmatizer.lemmatize(t) for t in query]
    expanded_query = query.copy()
    i = 0
    for word in query:
        if len(expanded_query) >= max_length:
            break
        # query expansion
        added_syns = []
        if wordnet.synsets(word):
            for syn in wordnet.synsets(word)[0].lemmas():
                syn_lem = lemmatizer.lemmatize(syn.name())
                if syn_lem != word:
                    expanded_query.insert(i + 1, syn_lem)
                    i += 1
    if len(expanded_query) > max_length:
        expanded_query = expanded_query[:max_length]

    query_ngrams = []
    for n in range(1, ngrams + 1):
        query_ngrams.extend([" ".join(ngram) for ngram in nltk.ngrams(expanded_query, n)])

    return query_ngrams

