import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

nltk.download('words')
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')

lemmatizer = WordNetLemmatizer()
stopwords = stopwords.words('english')


def tokenize(text: str, ngrams=1):
    text = text.lower().replace("tuebingen", "tübingen").replace("tubingen", "tübingen")
    tokens = nltk.tokenize.word_tokenize(text)
    cleaned_tokens = [lemmatizer.lemmatize(t) for t in tokens if t.isalnum() and t not in stopwords]
    if ngrams > 1:
        return [" ".join(t) for t in nltk.ngrams(cleaned_tokens, ngrams)]

    return cleaned_tokens
