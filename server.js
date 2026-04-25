const express = require('express');
const app = express();
const path = require('path');

app.set('view engine', 'ejs');
app.use(express.static('public'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 🛒 Items Data (Isse tu Admin Panel se badal sakta hai)
let products = [
    { id: 1, title: "OB53 VIP INJECTOR", price: "5.45", img: "https://via.placeholder.com/400x200" }
];

app.get('/', (req, res) => {
    res.render('index', { products });
});

// Admin Panel Access
app.get('/admin', (req, res) => {
    res.render('admin');
});

app.post('/add-item', (req, res) => {
    const { title, price, img } = req.body;
    products.push({ id: Date.now(), title, price, img });
    res.redirect('/');
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Aura Store Live: http://localhost:${PORT}`));
