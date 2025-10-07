import React from 'react'

interface Product {
  name: string;
  image_url: string;
  similarity: number;
}

interface ProductCardProps {
  product: Product;
}

export default function ProductCard({ product }: ProductCardProps) {
  const cardStyle: React.CSSProperties = {
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '1rem',
    margin: '0.5rem',
    width: '220px',
    textAlign: 'center',
    boxShadow: '0 2px 5px rgba(0,0,0,0.1)',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between'
  };

  const getImageUrl = (localPath: string) => {
    const relativePath = localPath.replace(/\\/g, '/');
    return `http://localhost:3000/images/${relativePath}`;
  };

  return (
    <div style={cardStyle}>
      <img src={getImageUrl(product.image_url)} alt={product.name} style={{ width: '100%', height: '200px', objectFit: 'cover', borderRadius: '4px' }} />
      <h3 style={{ fontSize: '1rem', margin: '10px 0 5px 0', color: '#333' }}>{product.name}</h3>
      <p style={{ fontSize: '0.9rem', color: '#666', margin: 0 }}>
        Similitud: <strong>{(product.similarity * 100).toFixed(1)}%</strong>
      </p>
    </div>
  )
}
