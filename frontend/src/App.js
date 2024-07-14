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
    <>
      <form onSubmit={handleSearch}>
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          placeholder="Search..."
        />
        <button type="submit">Search</button>
      </form>
      <div className="results">
        {results.length > 0 ? (
          <ul>
            {results.map((result, index) => (
              <li key={index}>{result.url}  {result.description}</li>
            ))}
          </ul>
        ) : (
          <p>No results found.</p>
        )}
      </div>
    </>
  )
}

export default App;
