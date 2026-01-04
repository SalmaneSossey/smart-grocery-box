const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const path = require('path');

const app = express();
app.use(cors());
app.use(bodyParser.json());

// Serve the static UI (index.html, assets, etc.)
app.use(express.static(path.join(__dirname, '../client')));

const port = process.env.PORT || 3000;

// In-memory storage (simple demo)
let products = [];
let orders = [];
let nextProductId = 1;

function normalizeProduct(p) {
  const id = (p && (p.id ?? p._id)) ?? nextProductId++;
  const name = (p && p.name) ?? 'Unknown';
  const price = Number((p && p.price) ?? 0);
  const unit = (p && (p.unit ?? p.units)) ?? '';
  const taken = Number((p && p.taken) ?? 1);
  const payable = Number((p && p.payable) ?? (price * taken));
  return { id, name, price, unit, taken, payable };
}

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../client/index.html'));
});

// Create a product (or overwrite same id)
app.post('/product', (req, res) => {
  const product = normalizeProduct(req.body);

  const idx = products.findIndex(p => String(p.id) === String(product.id));
  if (idx >= 0) products[idx] = product;
  else products.push(product);

  res.json(product);
});

// List products
app.get('/product', (req, res) => {
  res.json(products);
});

// Get product by id
app.get('/product/:id', (req, res) => {
  const id = req.params.id;
  const product = products.find(p => String(p.id) === String(id));
  if (!product) return res.status(404).json({ error: 'Not found' });
  res.json(product);
});

// Delete product by id
app.delete('/product/:id', (req, res) => {
  const id = req.params.id;
  products = products.filter(p => String(p.id) !== String(id));
  res.json({ ok: true });
});

// Update product by id
app.post('/product/:id', (req, res) => {
  const id = req.params.id;
  const existing = products.find(p => String(p.id) === String(id));
  if (!existing) return res.status(404).json({ error: 'Not found' });

  const patch = req.body || {};
  const updated = normalizeProduct({
    ...existing,
    ...patch,
    id: existing.id, // keep id stable
  });

  products = products.map(p => (String(p.id) === String(id) ? updated : p));
  res.json(updated);
});

// Checkout: freeze current cart into an order and clear cart
app.post('/checkout', (req, res) => {
  const total = products.reduce((s, p) => s + Number(p.payable || 0), 0);
  const order = {
    id: orders.length + 1,
    created_at: new Date().toISOString(),
    products: products,
    total: total
  };
  orders.push(order);
  products = [];
  res.json(order);
});

app.get('/checkout', (req, res) => {
  res.json(orders);
});

// Clear cart (DELETE all products)
app.delete('/cart', (req, res) => {
  products = [];
  res.json({ success: true, message: 'Cart cleared', cart: [] });
});

// Listen on all interfaces so your phone can access it
app.listen(port, '0.0.0.0', () => console.log(`Server listening on port ${port}!`));
