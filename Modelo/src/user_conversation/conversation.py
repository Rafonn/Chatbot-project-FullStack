import os
import pyodbc
from dotenv import load_dotenv

class Conversation:
    def __init__(self, message, user_id):
        load_dotenv()

        self.message = message
        self.user_id = user_id
        self.server   = os.getenv('DB_SERVER')
        self.database = os.getenv('DB_NAME')
        self.username = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.conn = self.connect_to_db()

    def connect_to_db(self):
        conn_str = (
            'DRIVER={ODBC Driver 17 for SQL Server};'
            f'SERVER={self.server};'
            f'DATABASE={self.database};'
            f'UID={self.username};'
            f'PWD={self.password};'
            'TrustServerCertificate=yes;'
        )
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
        cursor.execute("""
        IF NOT EXISTS (
            SELECT * 
            FROM sys.tables 
            WHERE name = 'bot_logs'
        )
        BEGIN
            CREATE TABLE bot_logs (
                id INT IDENTITY(1,1) PRIMARY KEY,
                userId NVARCHAR(50) NOT NULL,
                botMessage NVARCHAR(MAX) NOT NULL,
                userTimeStamp DATETIMEOFFSET NOT NULL 
                    DEFAULT SYSDATETIMEOFFSET()
            );
        END
        """)
        return conn

    def botResponse(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO bot_logs (userId, botMessage)
            OUTPUT INSERTED.botTimeStamp
            VALUES (?, ?);
        """, (self.user_id, self.message))
        inserted_ts = cursor.fetchone()[0]

        return {
            "botMessage": self.message,
            "botTimeStamp": inserted_ts
        }

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    conv = Conversation("Olá, mundo!", "usuario123")
    result = conv.botResponse()
    print(f"Bot enviou: {result['botMessage']} às {result['botTimeStamp']}")
    conv.close()
