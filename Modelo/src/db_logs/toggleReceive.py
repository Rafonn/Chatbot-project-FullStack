import os
import pyodbc
from dotenv import load_dotenv

class ToggleButtonStatus:
    def __init__(self, user_id):
        load_dotenv()

        self.server   = os.getenv('DB_SERVER')
        self.database = os.getenv('DB_NAME')
        self.username = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.user_id = user_id

        self.conn_str = (
            'DRIVER={ODBC Driver 17 for SQL Server};'
            f'SERVER={self.server};'
            f'DATABASE={self.database};'
            f'UID={self.username};'
            f'PWD={self.password};'
            'TrustServerCertificate=yes;'
        )
        self._ensure_table()

    def _ensure_table(self):
        with pyodbc.connect(self.conn_str, autocommit=True) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            IF NOT EXISTS (
                SELECT * FROM sys.tables 
                WHERE name = 'andritzButton_logs'
            )
            BEGIN
                CREATE TABLE andritzButton_logs (
                    userId      NVARCHAR(50) PRIMARY KEY,
                    buttonState BIT         NOT NULL DEFAULT(0),
                    updated_at  DATETIMEOFFSET NOT NULL 
                                DEFAULT SYSDATETIMEOFFSET()
                );
            END
            """)

    def fetch_status(self) -> bool:
        with pyodbc.connect(self.conn_str, autocommit=True) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT buttonState FROM andritzButton_logs WHERE userId = ?",
                self.user_id
            )
            row = cursor.fetchone()

            if row is None:
                cursor.execute(
                    "INSERT INTO andritzButton_logs (userId, buttonState) VALUES (?, 0)",
                    self.user_id
                )
                return False

            if(row[0] == '1'):
                boolButton = True
            else:
                boolButton = False

            return boolButton

if __name__ == "__main__":
    t = ToggleButtonStatus("0f572e6a-2e60-4ac6-b1d8-21ffd033f9f0")
    estado = t.fetch_status()
    print(f"Toggle para {t.user_id} está {'ON' if estado else 'OFF'}")
