import { useState } from 'react'
import './App.css';
import Document from './components/Document'

function App() {


  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [diversity, setDiversity] = useState(50);


  const handleSearch = async (e) => {
    e.preventDefault();
    if (loading) return;

    let method = e.target.elements.retrieval_method.value;
    let query = e.target.elements.query.value;
    let amount = e.target.elements.amount.value;

    if (!query) return;

    setResults([]);
    try {
      setLoading(true);
      const response = await fetch('/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          "query": query,
          "top_k": amount,
          "retrieval_method": method,
          "diversity": diversity/100
        }),
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Error fetching search results:', error);
    } finally {
      setLoading(false);
    }
  };


  return (
    <main>
      <div className='content'>
        <h1 className="logo">TüBing</h1>
        <form onSubmit={handleSearch}>
          <div className="search-box">
            <input
              id="query"
              type="text"
              placeholder="Search..."
            />
            <button type="submit"><img src="/search-icon.svg" alt="Search" className="search-icon" /></button>
          </div>

          <div className="query-options">
            <div>
              <label for="retrieval_method" value="retrieval_method">Method</label>
              <select name="retrieval_method" id="retrieval_method">
                <option value="bm25" selected>BM25</option>
                <option value="tfidf">TF-IDF</option>
              </select>
            </div>
            <div>
              <label for="amount" value="amount">Amount</label>
              <input id="amount"
                type="number"
                defaultValue="100"
                min="10"
                max="100" />
            </div>
            <div className="diversity-box">
              {/* <label for="rerank">rerank</label>
              <input type="checkbox" id="rerank" name="rerank"/> */}
              <label for="diversity">Priority</label>
              <div>
                <span>relevance</span>
                <input id="diversity"
                  type="range"
                  min="0"
                  max="100"
                  value={diversity}
                  onChange={e => setDiversity(e.target.value)} />
                <span>diversity</span>
              </div>
            </div>
          </div>

        </form>
        <div className="results">
          {loading && <span class="spinner"></span>}
          {(!loading && results?.length == 0) && <span>No results</span>}
          {results && (
            <ul className='results-list'>
              {results.map((doc, index) => (
                <li key={index}>
                  <Document doc={doc} />
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </main>
  )
}

export default App;
