import express from 'express';
import cors from 'cors';
import pg from 'pg';
import fs from 'fs';
import path from 'path';
import { marked } from 'marked';

const { Pool } = pg;
const app = express();
const port = 3000;

app.use(cors());
app.use(express.json());

const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'admin',
    password: process.env.DB_PASS || 'secret',
    database: process.env.DB_NAME || 'payments_db',
    port: 5432,
});

// Endpoint para Documentación
app.get('/docs', (req, res) => {
    const docsPath = path.join(process.cwd(), 'API_DOCS.md');
    try {
        const markdown = fs.readFileSync(docsPath, 'utf8');
        const htmlContent = marked(markdown);
        res.send(`
            <html>
                <head>
                    <title>API Docs - Payment Service</title>
                    <style>
                        body { font-family: sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; }
                        pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
                        code { font-family: monospace; color: #d63384; }
                        h1, h2, h3 { color: #007bff; }
                    </style>
                </head>
                <body>${htmlContent}</body>
            </html>
        `);
    } catch (err) {
        res.status(500).send('Error al cargar la documentación');
    }
});

// Health Check
app.get('/health', async (req, res) => {
    try {
        await pool.query('SELECT 1');
        res.json({ status: 'OK', database: 'Connected' });
    } catch (err) {
        res.status(500).json({ status: 'Error', database: 'Disconnected', error: (err as Error).message });
    }
});

// 1. Crear Usuario
app.post('/users', async (req, res) => {
    const { identity_token, initial_balance } = req.body;
    try {
        const result = await pool.query(
            'INSERT INTO users (identity_token, wallet_balance) VALUES ($1, $2) RETURNING *',
            [identity_token, initial_balance || 0.00]
        );
        res.status(201).json(result.rows[0]);
    } catch (err) {
        res.status(400).json({ error: (err as Error).message });
    }
});

// 2. Registrar Tarjeta NFC
app.post('/nfc/register', async (req, res) => {
    const { tag_id, user_id } = req.body;
    try {
        const result = await pool.query(
            'INSERT INTO nfc_cards (tag_id, user_id, status) VALUES ($1, $2, $3) RETURNING *',
            [tag_id, user_id, 'active']
        );
        res.status(201).json(result.rows[0]);
    } catch (err) {
        res.status(400).json({ error: (err as Error).message });
    }
});

// 3. Procesar Pago (Tap NFC/QR) - Transaccional ACID
app.post('/payments/tap', async (req, res) => {
    const { user_id, amount, transport_mode } = req.body;
    const client = await pool.connect();
    
    try {
        await client.query('BEGIN'); // Inicio de transacción ACID

        // 1. Verificar y descontar saldo
        const userRes = await client.query(
            'UPDATE users SET wallet_balance = wallet_balance - $1 WHERE id = $2 AND wallet_balance >= $1 RETURNING wallet_balance',
            [amount, user_id]
        );

        if (userRes.rowCount === 0) {
            throw new Error('Saldo insuficiente o usuario no encontrado');
        }

        // 2. Registrar transacción
        const transRes = await client.query(
            'INSERT INTO transactions (user_id, amount, transport_mode, status) VALUES ($1, $2, $3, $4) RETURNING *',
            [user_id, amount, transport_mode, 'completed']
        );

        await client.query('COMMIT'); // Commit si todo salió bien
        res.json({ message: 'Pago exitoso', balance: userRes.rows[0].wallet_balance, transaction: transRes.rows[0] });

    } catch (err) {
        await client.query('ROLLBACK'); // Rollback ante cualquier error
        res.status(400).json({ error: (err as Error).message });
    } finally {
        client.release();
    }
});

// 4. Obtener Historial de Usuario
app.get('/users/:id/transactions', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM transactions WHERE user_id = $1 ORDER BY transaction_time DESC', [req.params.id]);
        res.json(result.rows);
    } catch (err) {
        res.status(500).json({ error: (err as Error).message });
    }
});

app.listen(port, () => {
    console.log(`Payment Service listening at http://localhost:${port}`);
});
