// FILE: backend/server.js

const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json()); // Allow server to read JSON from requests

// --- Import Route Handlers ---
const processImageHandler = require('./routes/processImage');
const addManualEventHandler = require('./routes/addManualEvent');


// --- API Routes ---

// The OCR route now lives in its own file
app.post('/api/process-image', processImageHandler);

// The new route for manual entries
app.post('/api/add-manual-event', addManualEventHandler);


// --- Server Startup ---
const PORT = process.env.PORT || 5000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT} and listening on all network interfaces`);
});