const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 8080;
const DB_FILE = path.join(__dirname, 'database.json');

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' })); // Thumbnail image size limit

// Helper function to read database
const readDB = () => {
    if (!fs.existsSync(DB_FILE)) return [];
    const data = fs.readFileSync(DB_FILE);
    return JSON.parse(data);
};

// Helper function to write to database
const writeDB = (data) => {
    fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2));
};

// 1. GET Api - Saare products fetch karne ke liye
app.get('/api/products', (req, res) => {
    try {
        const products = readDB();
        res.json(products);
    } catch (error) {
        res.status(500).json({ error: "Database read error" });
    }
});

// 2. POST Api - Naya product add karne ke liye
app.post('/api/products', (req, res) => {
    try {
        const products = readDB();
        const newProduct = {
            id: Date.now().toString(), // Unique ID
            title: req.body.title,
            price: req.body.price,
            adsLink: req.body.adsLink,
            directLink: req.body.directLink,
            img: req.body.img || '' // Base64 image
        };
        products.push(newProduct);
        writeDB(products);
        res.status(201).json({ message: "Product added successfully!", product: newProduct });
    } catch (error) {
        res.status(500).json({ error: "Failed to save product" });
    }
});

// 3. DELETE Api - Product delete karne ke liye
app.delete('/api/products/:id', (req, res) => {
    try {
        let products = readDB();
        products = products.filter(p => p.id !== req.params.id);
        writeDB(products);
        res.json({ message: "Product deleted successfully!" });
    } catch (error) {
        res.status(500).json({ error: "Failed to delete product" });
    }
});

// Server start karna
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
         
