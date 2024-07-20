import { useState } from 'react'
import './App.css';
import Document from './components/Document'

function App() {


  const [query, setQuery] = useState('');
  const [amount, setAmount] = useState(100);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);


  const handleInputChange = (e) => {
    setQuery(e.target.value);
  };

  const handleSearch = async (e) => {
    if (loading) return;
    e.preventDefault();

    if (!query) return;

    setResults([]);
    try {
      setLoading(true);
      const response = await fetch('/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, "top_k": amount }),
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
              type="text"
              value={query}
              onChange={handleInputChange}
              placeholder="Search..."
            />
            <button type="submit"><img src="/search-icon.svg" alt="Search" className="search-icon" /></button>
          </div>

          <div className='amount-box'>
            <label for="top_k" value="Amount">Amount</label>
            <input id="top_k"
              type="number"
              min="10"
              max="100"
              value={amount}
              onChange={e => setAmount(e.target.value)} />
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
