import React, { useState } from 'react';
import './Document.css'

function Document({ doc }) {

  const MAX_DOC_DESC_LEN = 500;

  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);

  const [descAudioPlaying, setDescAudioPlaying] = useState(false);
  const [summaryAudioPlaying, setSummaryAudioPlaying] = useState(false);

  const textToSpeech = (text, onEnd) => {
    window.speechSynthesis.cancel();
    let synth = new SpeechSynthesisUtterance(text)
    synth.onend = onEnd;
    synth.lang = 'en-US';
    window.speechSynthesis.speak(synth);
  }

  const summarizeDoc = async (doc_url_hash) => {
    try {
      setSummaryLoading(true);
      const response = await fetch('/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ "url_hash": doc_url_hash }),
      });
      const data = await response.json();
      setSummary(data.summary);
    } catch (error) {
      console.error('Error getting summary:', error);
    } finally {
      setSummaryLoading(false);
    }
  }


  return (
    <>
      <a className='url-box' href={doc.url}>
        {doc.icon_url && <img src={doc.icon_url} />}
        <p>{doc.url}</p>
      </a>
      <a className="doc-title" href={doc.url}>{doc.title}</a>
      <div className="desc-box">
        {doc.description.length > 0 &&
          <div className={`speaker-box ${descAudioPlaying ? "playing" : ""}`}>
            <img
              className='speaker-icon'
              onClick={() => {
                setDescAudioPlaying(true);
                if(!descAudioPlaying){
                  textToSpeech(doc.title + "." + doc.description, () => setDescAudioPlaying(false));
                } else {
                  window.speechSynthesis.cancel();
                  setDescAudioPlaying(false);
                }
              }}
              src={'/speaker-icon.svg'} />
          </div>
        }
        <div>
          <p>{doc.description.substring(0, MAX_DOC_DESC_LEN)}{doc.description.length > MAX_DOC_DESC_LEN ? "..." : ""}</p>
        </div>
      </div>

      <div className="summary-box">
        {(!summary && !summaryLoading) &&
          <button
            onClick={() => summarizeDoc(doc.url_hash)}>Summarize</button>
        }
        {summary && (
          <>
            <div className={`speaker-box ${summaryAudioPlaying ? "playing" : ""}`}>
              <img
                className='speaker-icon'
                onClick={() => {
                  setSummaryAudioPlaying(true);
                  if(!summaryAudioPlaying){
                    textToSpeech(summary, () => setSummaryAudioPlaying(false));
                  } else {
                    window.speechSynthesis.cancel();
                    setSummaryAudioPlaying(false);
                  }
                }}
                src={'/speaker-icon.svg'} />
            </div>
            <div>
              <b className="summary-heading">Summary:</b>
              <p>{summary}</p>
            </div>
          </>
        )}
      </div>
      <div className="spinner-wrapper">
        {summaryLoading && <span class="spinner"></span>}
      </div>

    </>
  )
}
export default Document;