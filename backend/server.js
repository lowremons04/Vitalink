// FILE: backend/server.js

const express = require('express');
const cors = require('cors');
const multer = require('multer');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(cors());
app.use(express.json());

const uploadDir = 'uploads';
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir);
}
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadDir),
  filename: (req, file, cb) => cb(null, Date.now() + path.extname(file.originalname)),
});

// Use multer to handle multipart form data (image file + crop text field)
const upload = multer({ storage: storage });

app.post('/api/process-image', upload.single('image'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No image file provided.' });
  }
  if (!req.body.crop) {
    return res.status(400).json({ error: 'No crop data provided.' });
  }

  const imagePath = req.file.path;
  const cropData = JSON.parse(req.body.crop);

  // --- Spawn a Python child process with all necessary arguments ---
  const scriptPath = path.join(__dirname, 'digit_recognition_backend.py');
  
  const pythonArgs = [
    scriptPath,
    imagePath,
    String(Math.round(cropData.x)),
    String(Math.round(cropData.y)),
    String(Math.round(cropData.width)),
    String(Math.round(cropData.height))
  ];
  const pythonProcess = spawn('python', pythonArgs);

  let result = '';
  let error = '';

  pythonProcess.stdout.on('data', (data) => {
    result += data.toString();
  });

  pythonProcess.stderr.on('data', (data) => {
    error += data.toString();
  });

  pythonProcess.on('close', (code) => {
    fs.unlink(imagePath, (err) => {
      if (err) console.error("Error deleting file:", err);
    });

    if (code !== 0 || error) {
      console.error(`Python script error: ${error}`);
      return res.status(500).json({ error: 'Failed to process image.', details: error });
    }

    try {
      const jsonResult = JSON.parse(result);
      res.json(jsonResult);
    } catch (e) {
      console.error("Error parsing JSON from Python script:", e, "Raw output:", result);
      res.status(500).json({ error: 'Failed to parse the result from the script.', details: result });
    }
  });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT} and listening on all network interfaces`);
});