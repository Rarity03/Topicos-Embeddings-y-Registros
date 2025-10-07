import { useState, useRef } from 'react';
import ProductCard from './Components/ProductCard';

interface Product {
  name: string;
  image_url: string;
  similarity: number;
}

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() && !selectedFile) {
      setError('Por favor, ingresa un término de búsqueda o selecciona una imagen.');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    setResults([]);

    try {
      const apiUrl = `http://localhost:3000/search`;
      let response;

      if (selectedFile) {
        const formData = new FormData();
        formData.append('imageFile', selectedFile);
        response = await fetch(apiUrl, {
          method: 'POST',
          body: formData,
        });

      } else {
        response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            mode: 'texto',
            query: query
          }),
        });
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error);
      }

      const data: Product[] = await response.json();
      if (data.length === 0) {
        setError("No se encontraron resultados para tu búsqueda.");
      }
      setResults(data);

    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setQuery(''); 
      setPreviewUrl(URL.createObjectURL(file)); 
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    if(fileInputRef.current) {
      fileInputRef.current.value = ""; 
    }
  };

  return (
    <div style={{ 
      fontFamily: 'sans-serif', 
      maxWidth: '1200px', 
      margin: '0 auto', 
      padding: '2rem',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center', 
      justifyContent: 'center',
    }}>
      <header style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1>Buscador de Ropa Inteligente</h1>
        <p style={{ color: '#555' }}>Busca prendas por descripción</p>
      </header>

      <form onSubmit={handleSearch} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            if (selectedFile) clearFile(); 
          }}
          placeholder="Ej: sudadera negra con capucha"
          style={{ fontSize: '1rem', padding: '0.8rem', width: '400px', border: '1px solid #ccc', borderRadius: '8px 0 0 8px', outline: 'none' }}
          disabled={!!selectedFile}
        />
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept="image/*"
          style={{ display: 'none' }}
          id="imageUpload"
        />
        <label htmlFor="imageUpload" style={{ fontSize: '1rem', padding: '0.8rem 1rem', border: '1px solid #ccc', borderLeft: 'none', cursor: 'pointer', backgroundColor: '#f0f0f0' }}>
          🖼️
        </label>
        <button type="submit" disabled={isLoading} style={{ fontSize: '1rem', padding: '0.8rem 1.5rem', border: '1px solid #007bff', backgroundColor: '#007bff', color: 'white', borderRadius: '0 8px 8px 0', cursor: 'pointer', borderLeft: 'none' }}>
          {isLoading ? 'Buscando...' : 'Buscar'}
        </button>
      </form>

      {previewUrl && (
        <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
          <p>Buscando por imagen:</p>
          <img src={previewUrl} alt="Vista previa" style={{ maxHeight: '100px', borderRadius: '8px', border: '1px solid #ddd' }} />
          <button onClick={clearFile} style={{ display: 'block', margin: '0.5rem auto', background: 'none', border: 'none', color: 'red', cursor: 'pointer' }}>Quitar</button>
        </div>
      )}

      <div id="results-container">
        {error && <p style={{ color: 'red', textAlign: 'center' }}>{error}</p>}
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center' }}>
          {results.map((product, index) => (
            <ProductCard key={index} product={product} />
          ))}
        </div>
      </div>
    </div>
  )
}

export default App
