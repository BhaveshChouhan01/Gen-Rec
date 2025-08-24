import { useState } from "react";

const API = "http://localhost:8000/api";

export default function App() {
  const [activeSection, setActiveSection] = useState("home");
  const [query, setQuery] = useState("");
  const [images, setImages] = useState([]);
  const [file, setFile] = useState(null);
  const [ocrText, setOcrText] = useState("");
  const [pdfFile, setPdfFile] = useState(null);
  const [tables, setTables] = useState([]);
  const [prompt, setPrompt] = useState("");
  const [genImageUrl, setGenImageUrl] = useState("");
  const [loading, setLoading] = useState(false);
  
  const [question, setQuestion] = useState("What is in this image?");
  const [answer, setAnswer] = useState("");
  const [caption, setCaption] = useState("");

  const navItems = [
    { id: "home", label: "Home", icon: "🏠" },
    { id: "search", label: "Image Search", icon: "🔍" },
    { id: "ocr", label: "OCR", icon: "📝" },
    { id: "pdf", label: "PDF Tables", icon: "📊" },
    { id: "generate", label: "AI Generate", icon: "🎨" },
    { id: "vqa", label: "Visual Q&A", icon: "❓" }
  ];

  const doSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ q: query, limit: 12 }), // Increased limit for better grid
      });
      const data = await res.json();
      setImages(data.results || []);
    } catch (error) {
      console.error("Search failed:", error);
      setImages([]); // Clear results on error
    }
    setLoading(false);
  };

  const doOCR = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${API}/ocr`, { method: "POST", body: fd });
      const data = await res.json();
      setOcrText(data.text || "");
    } catch (error) {
      console.error("OCR failed:", error);
    }
    setLoading(false);
  };

  const askVQA = async (url) => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/vqa`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_url: url, question }),
      });
      const data = await res.json();
      setAnswer(data.answer || "");
      setCaption(data.caption || "");
      setActiveSection("vqa");
    } catch (error) {
      console.error("VQA failed:", error);
    }
    setLoading(false);
  };

  const doPDF = async () => {
    if (!pdfFile) return;
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append("file", pdfFile);
      const res = await fetch(`${API}/ocr-pdf`, { method: "POST", body: fd });
      const data = await res.json();
      setTables(data.tables || []);
    } catch (error) {
      console.error("PDF processing failed:", error);
    }
    setLoading(false);
  };

  const doGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();
      setGenImageUrl(`http://localhost:8000${data.image_url}`);
    } catch (error) {
      console.error("Generation failed:", error);
    }
    setLoading(false);
  };

  const renderHome = () => (
    <div className="home-section">
      <div className="hero-card">
        <div className="hero-content">
          <h1 className="hero-title">🚀 Image Understanding MVP</h1>
          <p className="hero-subtitle">
            Powerful AI-driven image analysis, OCR, and generation tools all in one place
          </p>
          <div className="feature-grid">
            <div className="feature-card" onClick={() => setActiveSection("search")}>
              <div className="feature-icon">🔍</div>
              <h3>Image Search</h3>
              <p>Search through millions of images with advanced AI</p>
            </div>
            <div className="feature-card" onClick={() => setActiveSection("ocr")}>
              <div className="feature-icon">📝</div>
              <h3>OCR Technology</h3>
              <p>Extract text from any image with high accuracy</p>
            </div>
            <div className="feature-card" onClick={() => setActiveSection("pdf")}>
              <div className="feature-icon">📊</div>
              <h3>PDF Tables</h3>
              <p>Extract structured data from PDF documents</p>
            </div>
            <div className="feature-card" onClick={() => setActiveSection("generate")}>
              <div className="feature-icon">🎨</div>
              <h3>AI Generation</h3>
              <p>Create stunning images from text descriptions</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderSearch = () => (
    <div className="section">
      <div className="section-header">
        <h2>🔍 Image Search</h2>
        <p>Discover images using advanced AI-powered search</p>
      </div>
      <div className="card">
        <div className="search-container">
          <input 
            className="input search-input" 
            placeholder="What are you looking for? (e.g., sunset, cat, technology...)" 
            value={query} 
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && doSearch()}
          />
          <button className="btn blue search-btn" onClick={doSearch} disabled={loading}>
            {loading ? "🔄 Searching..." : "🔍 Search"}
          </button>
        </div>
      </div>
      
      {loading && (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Searching for amazing images...</p>
        </div>
      )}
      
      {images.length > 0 && !loading && (
        <div className="results-container">
          <div className="results-header">
            <h3>Search Results ({images.length})</h3>
          </div>
          <div className="image-grid">
            {images.map((img, i) => (
              <div key={i} className="image-card">
                <div className="image-container">
                  <img 
                    className="image-thumb" 
                    src={img.thumbnail || img.url} 
                    alt={img.title || `Image ${i + 1}`}
                    loading="lazy"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'flex';
                    }}
                  />
                  <div className="image-placeholder" style={{display: 'none'}}>
                    <div className="placeholder-icon">🖼️</div>
                    <p>Image unavailable</p>
                  </div>
                </div>
                <div className="image-info">
                  <div className="provider-badge">{img.provider}</div>
                  {img.title && <p className="image-title">{img.title}</p>}
                  <div className="image-actions">
                    <button className="btn green small" onClick={() => askVQA(img.url)}>
                      💬 Ask Question
                    </button>
                    <a href={img.url} target="_blank" rel="noopener noreferrer" className="btn blue small">
                      🔗 View Full
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {images.length === 0 && !loading && query && (
        <div className="no-results">
          <div className="no-results-icon">🔍</div>
          <h3>No results found</h3>
          <p>Try searching for something else, like "nature", "technology", or "animals"</p>
        </div>
      )}
    </div>
  );

  const renderOCR = () => (
    <div className="section">
      <div className="section-header">
        <h2>📝 OCR - Text Extraction</h2>
        <p>Extract text from images with high precision</p>
      </div>
      <div className="card">
        <div className="upload-area">
          <input 
            type="file" 
            accept="image/*" 
            onChange={e => setFile(e.target.files?.[0] || null)}
            className="file-input"
            id="image-upload"
          />
          <label htmlFor="image-upload" className="upload-label">
            📸 Choose Image File
          </label>
          {file && <span className="file-name">{file.name}</span>}
          <button className="btn warn" onClick={doOCR} disabled={!file || loading}>
            {loading ? "⏳ Processing..." : "🚀 Extract Text"}
          </button>
        </div>
        {ocrText && (
          <div className="result-container">
            <h4>Extracted Text:</h4>
            <div className="pre">{ocrText}</div>
          </div>
        )}
      </div>
    </div>
  );

  const renderPDF = () => (
    <div className="section">
      <div className="section-header">
        <h2>📊 PDF Table Extraction</h2>
        <p>Extract structured data from PDF documents</p>
      </div>
      <div className="card">
        <div className="upload-area">
          <input 
            type="file" 
            accept="application/pdf" 
            onChange={e => setPdfFile(e.target.files?.[0] || null)}
            className="file-input"
            id="pdf-upload"
          />
          <label htmlFor="pdf-upload" className="upload-label">
            📄 Choose PDF File
          </label>
          {pdfFile && <span className="file-name">{pdfFile.name}</span>}
          <button className="btn warn" onClick={doPDF} disabled={!pdfFile || loading}>
            {loading ? "⏳ Processing..." : "📊 Extract Tables"}
          </button>
        </div>
        {tables.length > 0 && (
          <div className="result-container">
            <h4>Extracted Tables:</h4>
            <div className="table-links">
              {tables.map((t, idx) => (
                <a 
                  key={idx} 
                  href={`http://localhost:8000${t}`} 
                  target="_blank" 
                  rel="noreferrer"
                  className="table-link"
                >
                  📈 {t.split("/").pop()}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderGenerate = () => (
    <div className="section">
      <div className="section-header">
        <h2>🎨 AI Image Generation</h2>
        <p>Create stunning images from text descriptions</p>
      </div>
      <div className="card">
        <div className="generate-container">
          <textarea 
            className="input generate-input" 
            placeholder="Describe the image you want to create... (e.g., A futuristic city at sunset with flying cars)"
            value={prompt} 
            onChange={e => setPrompt(e.target.value)}
            rows={3}
          />
          <button className="btn green" onClick={doGenerate} disabled={loading}>
            {loading ? "🎨 Creating..." : "✨ Generate Image"}
          </button>
        </div>
        {genImageUrl && (
          <div className="generated-result">
            <h4>Generated Image:</h4>
            <img src={genImageUrl} alt="generated" className="generated-image" />
            <a href={genImageUrl} download className="btn blue">💾 Download</a>
          </div>
        )}
      </div>
    </div>
  );

  const renderVQA = () => (
    <div className="section">
      <div className="section-header">
        <h2>❓ Visual Question & Answer</h2>
        <p>Ask questions about images and get intelligent answers</p>
      </div>
      <div className="card">
        <div className="vqa-container">
          <label>Your Question:</label>
          <input 
            className="input" 
            value={question} 
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="What would you like to know about the image?"
          />
        </div>
        {(answer || caption) && (
          <div className="answer-container">
            {caption && (
              <div className="caption-result">
                <h4>🖼️ Image Description:</h4>
                <p>{caption}</p>
              </div>
            )}
            {answer && (
              <div className="answer-result">
                <h4>💬 Answer:</h4>
                <p>{answer}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );

  const renderContent = () => {
    switch(activeSection) {
      case "home": return renderHome();
      case "search": return renderSearch();
      case "ocr": return renderOCR();
      case "pdf": return renderPDF();
      case "generate": return renderGenerate();
      case "vqa": return renderVQA();
      default: return renderHome();
    }
  };

  return (
    <div className="app">
      {/* Navigation */}
      <nav className="navbar">
        <div className="nav-container">
          <div className="nav-brand" onClick={() => setActiveSection("home")}>
            🖼️ Image Understanding MVP
          </div>
          <div className="nav-links">
            {navItems.map(item => (
              <button
                key={item.id}
                className={`nav-item ${activeSection === item.id ? 'active' : ''}`}
                onClick={() => setActiveSection(item.id)}
              >
                <span className="nav-icon">{item.icon}</span>
                <span className="nav-label">{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container">
        {renderContent()}
      </main>

      <style jsx>{`
        .app {
          min-height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        .container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 0 24px;
        }

        .card {
          background: rgba(255, 255, 255, 0.15);
          backdrop-filter: blur(20px);
          border-radius: 20px;
          padding: 32px;
          border: 1px solid rgba(255, 255, 255, 0.2);
          box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        }

        .input {
          width: 100%;
          padding: 16px 20px;
          border: 2px solid rgba(255, 255, 255, 0.2);
          border-radius: 12px;
          background: rgba(255, 255, 255, 0.1);
          color: white;
          font-size: 16px;
          outline: none;
          transition: all 0.3s ease;
        }

        .input::placeholder {
          color: rgba(255, 255, 255, 0.6);
        }

        .input:focus {
          border-color: rgba(255, 255, 255, 0.5);
          background: rgba(255, 255, 255, 0.15);
        }

        .btn {
          padding: 12px 24px;
          border: none;
          border-radius: 12px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
        }

        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn.small {
          padding: 8px 16px;
          font-size: 14px;
        }

        .btn.blue {
          background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
          color: white;
        }

        .btn.blue:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
        }

        .btn.green {
          background: linear-gradient(135deg, #10b981 0%, #047857 100%);
          color: white;
        }

        .btn.green:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
        }

        .btn.warn {
          background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
          color: white;
        }

        .btn.warn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(245, 158, 11, 0.4);
        }

        .navbar {
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(20px);
          border-bottom: 1px solid rgba(255, 255, 255, 0.2);
          padding: 0;
          position: sticky;
          top: 0;
          z-index: 100;
        }

        .nav-container {
          max-width: 1200px;
          margin: 0 auto;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 24px;
        }

        .nav-brand {
          font-size: 20px;
          font-weight: 900;
          color: white;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .nav-brand:hover {
          transform: scale(1.05);
        }

        .nav-links {
          display: flex;
          gap: 8px;
        }

        .nav-item {
          background: transparent;
          border: none;
          color: rgba(255, 255, 255, 0.8);
          padding: 12px 16px;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 600;
        }

        .nav-item:hover {
          background: rgba(255, 255, 255, 0.1);
          color: white;
          transform: translateY(-2px);
        }

        .nav-item.active {
          background: rgba(255, 255, 255, 0.2);
          color: white;
        }

        .nav-icon {
          font-size: 18px;
        }

        .home-section {
          padding: 60px 0;
        }

        .hero-card {
          background: rgba(255, 255, 255, 0.15);
          backdrop-filter: blur(20px);
          border-radius: 24px;
          padding: 60px;
          text-align: center;
          border: 1px solid rgba(255, 255, 255, 0.2);
          box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        }

        .hero-title {
          font-size: 48px;
          font-weight: 900;
          margin-bottom: 16px;
          background: linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.8) 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .hero-subtitle {
          font-size: 20px;
          color: rgba(255, 255, 255, 0.9);
          margin-bottom: 40px;
        }

        .feature-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 24px;
          margin-top: 40px;
        }

        .feature-card {
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
          border-radius: 16px;
          padding: 32px 24px;
          text-align: center;
          cursor: pointer;
          transition: all 0.3s ease;
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .feature-card:hover {
          transform: translateY(-8px);
          background: rgba(255, 255, 255, 0.15);
          box-shadow: 0 16px 40px rgba(31, 38, 135, 0.5);
        }

        .feature-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }

        .feature-card h3 {
          color: white;
          margin-bottom: 12px;
          font-weight: 700;
        }

        .feature-card p {
          color: rgba(255, 255, 255, 0.8);
          font-size: 14px;
        }

        .section {
          padding: 40px 0;
        }

        .section-header {
          text-align: center;
          margin-bottom: 40px;
        }

        .section-header h2 {
          font-size: 36px;
          font-weight: 800;
          color: white;
          margin-bottom: 8px;
        }

        .section-header p {
          color: rgba(255, 255, 255, 0.8);
          font-size: 16px;
        }

        .search-container {
          display: flex;
          gap: 16px;
          align-items: center;
        }

        .search-input {
          flex: 1;
        }

        .loading-container {
          text-align: center;
          padding: 40px;
          color: white;
        }

        .loading-spinner {
          width: 40px;
          height: 40px;
          border: 4px solid rgba(255, 255, 255, 0.3);
          border-top: 4px solid white;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 16px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .results-container {
          margin-top: 32px;
        }

        .results-header {
          margin-bottom: 24px;
        }

        .results-header h3 {
          color: white;
          font-weight: 700;
          font-size: 24px;
        }

        .image-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 24px;
          margin-top: 24px;
        }

        .image-card {
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
          border-radius: 16px;
          overflow: hidden;
          border: 1px solid rgba(255, 255, 255, 0.1);
          transition: all 0.3s ease;
        }

        .image-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 16px 40px rgba(31, 38, 135, 0.5);
        }

        .image-container {
          position: relative;
          width: 100%;
          height: 200px;
          overflow: hidden;
        }

        .image-thumb {
          width: 100%;
          height: 100%;
          object-fit: cover;
          transition: transform 0.3s ease;
        }

        .image-card:hover .image-thumb {
          transform: scale(1.05);
        }

        .image-placeholder {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(255, 255, 255, 0.1);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: rgba(255, 255, 255, 0.6);
        }

        .placeholder-icon {
          font-size: 48px;
          margin-bottom: 8px;
        }

        .image-info {
          padding: 16px;
        }

        .provider-badge {
          background: rgba(255, 255, 255, 0.2);
          color: white;
          padding: 4px 8px;
          border-radius: 8px;
          font-size: 12px;
          font-weight: 600;
          margin-bottom: 8px;
          display: inline-block;
          text-transform: uppercase;
        }

        .image-title {
          color: rgba(255, 255, 255, 0.9);
          font-size: 14px;
          margin-bottom: 12px;
          line-height: 1.4;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .image-actions {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .no-results {
          text-align: center;
          padding: 60px 20px;
          color: white;
        }

        .no-results-icon {
          font-size: 64px;
          margin-bottom: 16px;
          opacity: 0.6;
        }

        .no-results h3 {
          font-size: 24px;
          margin-bottom: 8px;
          font-weight: 700;
        }

        .no-results p {
          color: rgba(255, 255, 255, 0.8);
          font-size: 16px;
        }

        .upload-area {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
        }

        .file-input {
          display: none;
        }

        .upload-label {
          background: rgba(255, 255, 255, 0.1);
          border: 2px dashed rgba(255, 255, 255, 0.3);
          border-radius: 16px;
          padding: 40px;
          text-align: center;
          cursor: pointer;
          transition: all 0.3s ease;
          color: white;
          font-weight: 600;
          min-width: 200px;
        }

        .upload-label:hover {
          background: rgba(255, 255, 255, 0.15);
          border-color: rgba(255, 255, 255, 0.5);
        }

        .file-name {
          color: rgba(255, 255, 255, 0.8);
          font-size: 14px;
          background: rgba(255, 255, 255, 0.1);
          padding: 8px 16px;
          border-radius: 8px;
        }

        .result-container {
          margin-top: 24px;
        }

        .result-container h4 {
          color: white;
          margin-bottom: 16px;
          font-weight: 700;
        }

        .pre {
          background: rgba(0, 0, 0, 0.3);
          border-radius: 12px;
          padding: 20px;
          color: #f8f9fa;
          font-family: 'Courier New', monospace;
          white-space: pre-wrap;
          word-wrap: break-word;
          max-height: 300px;
          overflow-y: auto;
        }

        .generate-container {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .generate-input {
          resize: vertical;
          font-family: inherit;
          min-height: 100px;
        }

        .generated-result {
          margin-top: 24px;
          text-align: center;
        }

        .generated-result h4 {
          color: white;
          margin-bottom: 16px;
        }

        .generated-image {
          max-width: 100%;
          max-height: 500px;
          border-radius: 16px;
          margin: 16px 0;
          box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }

        .vqa-container {
          margin-bottom: 24px;
        }

        .vqa-container label {
          color: white;
          font-weight: 600;
          margin-bottom: 8px;
          display: block;
        }

        .answer-container {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 16px;
          padding: 24px;
          margin-top: 24px;
        }

        .caption-result, .answer-result {
          margin-bottom: 16px;
        }

        .caption-result:last-child, .answer-result:last-child {
          margin-bottom: 0;
        }

        .caption-result h4, .answer-result h4 {
          color: white;
          margin-bottom: 8px;
          font-weight: 700;
        }

        .caption-result p, .answer-result p {
          color: rgba(255, 255, 255, 0.9);
          line-height: 1.6;
          font-size: 16px;
        }

        .table-links {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
        }

        .table-link {
          background: rgba(255, 255, 255, 0.1);
          color: white;
          padding: 12px 20px;
          border-radius: 8px;
          text-decoration: none;
          font-weight: 600;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .table-link:hover {
          background: rgba(255, 255, 255, 0.2);
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }

        @media (max-width: 768px) {
          .nav-links {
            flex-wrap: wrap;
            gap: 4px;
          }
          
          .nav-item {
            padding: 8px 12px;
          }
          
          .nav-label {
            display: none;
          }
          
          .hero-card {
            padding: 40px 24px;
          }
          
          .hero-title {
            font-size: 32px;
          }
          
          .search-container {
            flex-direction: column;
          }

          .search-input {
            margin-bottom: 8px;
          }

          .image-grid {
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 16px;
          }

          .container {
            padding: 0 16px;
          }

          .feature-grid {
            grid-template-columns: 1fr;
          }

          .image-actions {
            flex-direction: column;
          }
        }

        @media (max-width: 480px) {
          .image-grid {
            grid-template-columns: 1fr;
          }

          .nav-container {
            flex-direction: column;
            gap: 16px;
          }

          .nav-links {
            justify-content: center;
          }
        }
      `}</style>
    </div>
  );
}