import sql from 'mssql';
import dotenv from 'dotenv';

dotenv.config();

const config = {
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  server: process.env.DB_SERVER,
  database: process.env.DB_NAME,
  options: {
    encrypt: false,
    trustServerCertificate: true
  }
};

let pool = null;

async function connectToSqlServer() {
  if (pool && pool.connected) {
    return pool;
  }
  pool = await sql.connect(config);
  return pool;
}

export default connectToSqlServer