const express = require('express');
const mongoose = require('mongoose');
const app = express();
require('dotenv').config();

app.set('view engine', 'ejs');
app.use(express.static('public'));
app.use(express.json());

// 🔗 DATABASE CONNECTION (MongoDB Atlas use karenge)
// Yahan tum apna MongoDB URL daloge baad mein
const dbURI = process.env.MONGO_URI || "your_mongodb_connection_string";

let products = [
    { title: "V-Badge Elite", price: "5.00", img: "https://i.ibb.co/example.jpg" }
];

app.get('/', (req, res) => {
    res.render('index', { products });
});

// Admin Login Logic
app.post('/admin-login', (req, res) => {
    const { user, pass } = req.body;
    if(user === "admin" && pass === "alok123") {
        res.json({ success: true });
    } else {
        res.json({ success: false });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Aura Store Live on ${PORT}`));
