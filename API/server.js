require('dotenv').config();

const express = require("express");
const cors = require("cors");
const http = require("http");
const WebSocket = require("ws");
const sql = require("mssql");
const url = require("url");

const app = express();
const port = process.env.PORT;

const dbConfig = {
  user: process.env.DB_USER_DEV,
  password: process.env.DB_PASSWORD,
  server: process.env.DB_SERVER_DEV,
  database: process.env.DB_NAME,
  options: {
    encrypt: false,
    trustServerCertificate: true
  }
};

const pool = new sql.ConnectionPool(dbConfig);
pool.connect()
  .then(() => console.log('Conectado ao SQL Server'))
  .catch(err => console.error('Erro ao conectar ao SQL Server:', err));

app.use(express.json());
app.use(cors());

const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

wss.on("connection", (ws, req) => {
  ws.isAlive = true;

  // toda vez que o cliente responder um pong, marca de novo como vivo
  ws.on("pong", () => {
    ws.isAlive = true;
  });

  // a cada 30s, varre todos os sockets:
  // - se ainda não respondeu ao último ping, encerra
  // - senão, zera o flag e manda novo ping
  const heartbeatInterval = setInterval(() => {
    wss.clients.forEach(client => {
      if (client.isAlive === false) {
        return client.terminate();
      }
      client.isAlive = false;
      client.ping();
    });
  }, 30000);

  const { userId, lastTimestamp } = url.parse(req.url, true).query;
  if (!userId) {
    ws.send(JSON.stringify({ error: "Parâmetro 'userId' na query é obrigatório." }));
    return ws.close();
  }

  let lastTs = lastTimestamp ? new Date(lastTimestamp) : new Date(0);

  async function fetchLatestBotLog() {
    const result = await pool.request()
      .input("userId", sql.NVarChar(50), userId)
      .query(`
        SELECT TOP 1 botMessage, botTimeStamp
        FROM bot_logs
        WHERE userId = @userId
        ORDER BY botTimeStamp DESC
      `);
    return result.recordset[0];
  }

  const intervalId = setInterval(async () => {
    try {
      const latest = await fetchLatestBotLog();
      if (latest) {
        const ts = new Date(latest.botTimeStamp);
        if (ts > lastTs) {
          lastTs = ts;

          ws.send(JSON.stringify({
            botMessage: latest.botMessage,
            botTimeStamp: latest.botTimeStamp
          }));
        }
      }
    } catch (err) {
      console.error("Erro ao buscar log do bot:", err);
      ws.send(JSON.stringify({ error: "Erro interno ao buscar log." }));
    }
  }, 1000);

  ws.on("close", () => {
    clearInterval(heartbeatInterval);
    clearInterval(intervalId);
  });
});

// ————————————— REST Routes ————————————— \\

app.post("/logs/user", async (req, res) => {
  try {
    const { log, userId } = req.body;
    if (!log || !userId) {
      return res.status(400).json({ error: "Campos 'log' e 'userId' são obrigatórios." });
    }
    const timestamp = new Date().toISOString();

    await pool.request()
      .input('log', sql.NVarChar(sql.MAX), log)
      .input('userId', sql.NVarChar(50), userId)
      .input('timestamp', sql.DateTimeOffset, timestamp)
      .query(`
        INSERT INTO user_logs (userMessage, userId, userTimeStamp)
        VALUES (@log, @userId, @timestamp)
      `);

    res.status(200).json({ message: "Log do usuário inserido com sucesso." });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Erro ao salvar o log do usuário no banco de dados." });
  }
});

app.get("/logs/bot/:userId", async (req, res) => {
  const { userId } = req.params;
  if (!userId) {
    return res.status(400).json({ error: "Parâmetro 'userId' é obrigatório." });
  }
  try {
    const result = await pool.request()
      .input("userId", sql.NVarChar(50), userId)
      .query(`
        SELECT TOP 1 botMessage
        FROM bot_logs
        WHERE userId = @userId
        ORDER BY botTimeStamp DESC
      `);
    if (!result.recordset.length) {
      return res.status(404).json({ message: "Nenhum log encontrado para este usuário." });
    }
    res.json({ lastLog: result.recordset[0].botMessage });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Erro ao buscar o log no banco de dados." });
  }
});

app.get("/logs/user/:userId", async (req, res) => {
  const { userId } = req.params;
  if (!userId) {
    return res.status(400).json({ error: "Parâmetro 'userId' é obrigatório." });
  }
  try {
    const result = await pool.request()
      .input('userId', sql.NVarChar(50), userId)
      .query(`
        SELECT TOP 1 userMessage
        FROM user_logs
        WHERE userId = @userId
        ORDER BY userTimeStamp DESC
      `);
    if (!result.recordset.length) {
      return res.status(404).json({ message: "Nenhum log encontrado para este usuário." });
    }
    res.json({ lastLog: result.recordset[0].userMessage });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Erro ao buscar o log do usuário no banco de dados." });
  }
});

app.get("/", (req, res) => {
  res.json({ message: "API Online!" });
});

server.listen(port, '0.0.0.0', () => {
});
