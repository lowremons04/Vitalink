// FILE: backend/server.js

const express = require('express');
const cors = require('cors');
require('dotenv').config();

const getHealthEvents = require('./routes/getHealthEvents');
const addManualEvent = require('./routes/addManualEvent');
const processImage = require('./routes/processImage');

const app = express();
app.use(cors());
app.use(express.json());

app.get('/api/health-events', getHealthEvents);
app.post('/api/add-manual-event', addManualEvent);
app.post('/api/process-image', processImage);

app.get('/', (req, res) => {
  res.send('Hello from backend!');
});

// Use Render's port, or 5000 for local development
const PORT = process.env.PORT || 5000;

// Listen on all available network interfaces
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server is running on port ${PORT}`);
});
