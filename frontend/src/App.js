import { useState } from 'react'
import './App.css';


function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const handleInputChange = (e) => {
    setQuery(e.target.value);
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setResults([]);
    try {
      const response = await fetch('/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Error fetching search results:', error);
    }
  };

  return (
    <main>
      <div className='content'>
        <h1 className="logo">TüBing</h1>
        <form className="search-box" onSubmit={handleSearch}>
          <input
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder="Search..."
          />
          <button type="submit"><img src="/search-icon.svg" alt="Search" className="search-icon" /></button>
        </form>
        <div className="results">
          {results ? (
            <ul className='results-list'>
              {results.map((doc, index) => (
                <li key={index}>
                  <a className='url-box' href={doc.url}>
                    <img src={doc.icon_url} />
                    <p>{doc.url}</p>
                  </a>
                  <a className="doc-title" href={doc.url}>{doc.title}</a>
                  <p>{doc.description}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p>No results found.</p>
          )}
        </div>
      </div>
    </main>
  )
}

export default App;
