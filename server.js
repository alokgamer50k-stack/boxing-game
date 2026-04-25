const express = require('express');
const cors = require('cors');
const app = express();

// 🔓 Sabse Important: Ye har jagah se request allow karega
app.use(cors({
    origin: '*',
    methods: ['GET', 'POST']
}));

app.use(express.json());

let storeData = [
    { title: "Elite Headshot v1", price: "5.00", link: "https://t.me/.." }
];

// Home page par ek message (Checking ke liye)
app.get('/', (req, res) => {
    res.send("<h1>Backend Brain is Online!</h1><p>Try /api/items to see data.</p>");
});

app.get('/api/items', (req, res) => {
    res.json(storeData);
});

app.post('/api/add', (req, res) => {
    const { title, price, link, password } = req.body;
    if(password === "alok123") {
        storeData.push({ title, price, link });
        res.json({ success: true });
    } else {
        res.json({ success: false, message: "Wrong Password" });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log("Server Active!"));
