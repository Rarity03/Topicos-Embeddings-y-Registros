const express = require('express');
const cors = require('cors');
const pg = require('pg');
const multer = require('multer');
const fs = require('fs');
const { spawn } = require('child_process');
const { toSql, registerType } = require('pgvector/pg');
const path = require('path');

const app = express();
const PORT = 3000;

const UPLOADS_DIR = path.join(__dirname, 'uploads');
if (!fs.existsSync(UPLOADS_DIR)) {
  fs.mkdirSync(UPLOADS_DIR);
}
const upload = multer({ dest: UPLOADS_DIR });

app.use(cors());
app.use(express.json());

const imagesDirectory = path.join(__dirname, '..', '..', 'Imagenes Ropa');
app.use('/images', express.static(imagesDirectory));


const pool = new pg.Pool({
  user: 'postgres',
  host: 'localhost',
  database: 'ropa_db',
  password: '12345', 
  port: 5434,         
});


function getEmbeddingFromPython(mode, query) {
  return new Promise((resolve, reject) => {

    const pythonProcess = spawn('python', [
        '../busqueda.py', 
        mode, 
        query
    ]);

    let embeddingJson = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
      embeddingJson += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        return reject(new Error(`El script de Python falló con código ${code}: ${errorOutput}`));
      }
      try {
        const embedding = JSON.parse(embeddingJson);
        resolve(embedding);
      } catch (e) {
        reject(new Error(`Error al parsear el JSON del embedding: ${e.message}`));
      }
    });
  });
}

app.post('/search', upload.single('imageFile'), async (req, res) => {
  
  let mode, query;
  const { threshold = 0.5, limit = 20 } = req.body;
  if (req.file) {
    mode = 'imagen';
    query = req.file.path; 
  } else if (req.body.query) {
    mode = 'texto';
    query = req.body.query;
  } else {
    return res.status(400).json({ error: "Se requiere un 'query' de texto o un archivo de imagen" });
  }
  
  if (!mode || !query) {
    return res.status(400).json({ error: "Parámetros inválidos para la búsqueda." });
  }
  
  try {
    const queryEmbedding = await getEmbeddingFromPython(mode, query);
    const embeddingVector = toSql(queryEmbedding);

    const client = await pool.connect();
    await registerType(client);

    const sqlQuery = `
      SELECT p.name, p.image_url, 1 - (pv.embedding <=> $1) AS similarity
      FROM Products p
      JOIN ProductVectors pv ON p.product_id = pv.product_id
      WHERE 1 - (pv.embedding <=> $1) > $2
      ORDER BY similarity DESC
      LIMIT $3;
    `;
    const { rows } = await client.query(sqlQuery, [embeddingVector, threshold, limit]);
    client.release();
    res.json(rows);
    if (req.file) {
      fs.unlinkSync(req.file.path);
    }

  } catch (error) {
    res.status(500).json({ error: 'Ocurrió un error en el servidor durante la búsqueda.', details: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Servidor corriendo en http://localhost:${PORT}`);
});
