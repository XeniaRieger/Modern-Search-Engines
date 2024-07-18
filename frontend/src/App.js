import { useState } from 'react'
import './App.css';

function App() {

  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  function textToSpeech(text) {
    window.speechSynthesis.cancel();
    let synth = new SpeechSynthesisUtterance(text)
    synth.lang = 'en-US';
    window.speechSynthesis.speak(synth);
  }

  const handleInputChange = (e) => {
    setQuery(e.target.value);
  };

  const handleSearch = async (e) => {
    if(loading) return;
    e.preventDefault();

    if(!query) return;

    setResults([]);
    try {
      setLoading(true);
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
    } finally {
      setLoading(false);
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
          {loading && <span class="spinner"></span>}
          {(!loading && results?.length == 0) && <span>No results</span>}
          {results && (
            <ul className='results-list'>
              {results.map((doc, index) => (
                <li key={index}>
                  <a className='url-box' href={doc.url}>
                    {doc.icon_url && <img src={doc.icon_url} />}
                    <p>{doc.url}</p>
                  </a>
                  <a className="doc-title" href={doc.url}>{doc.title}</a>
                  <div className="desc-box">
                    {doc.description.length > 0 &&
                      <img 
                        className="speaker-icon"
                        onClick={() => textToSpeech(doc.description)} 
                        src={'/speaker-icon.svg'}/>
                    }
                    <p>{doc.description.substring(0, 550)}{doc.description.length > 550 ? "...":""}</p>
                  </div>
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
