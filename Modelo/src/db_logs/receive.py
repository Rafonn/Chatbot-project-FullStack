import os
import pyodbc
from dotenv import load_dotenv

class LastMessageFetcher:
    def __init__(self, user_id):
        load_dotenv()

        self.server   = os.getenv('DB_SERVER')
        self.database = os.getenv('DB_NAME')
        self.username = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.user_id  = user_id
        self.last_message_timestamp = None

        self.conn_str = (
            'DRIVER={ODBC Driver 17 for SQL Server};'
            f'SERVER={self.server};'
            f'DATABASE={self.database};'
            f'UID={self.username};'
            f'PWD={self.password};'
            'TrustServerCertificate=yes;'
        )

    def fetch_last_message(self):
        with pyodbc.connect(self.conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 
                  userTimeStamp, 
                  userMessage 
                FROM user_logs 
                WHERE userId = ? 
                ORDER BY userTimeStamp DESC
            """, self.user_id)
            row = cursor.fetchone()

        if row:
            userTimeStamp, userMessage = row
            if userTimeStamp != self.last_message_timestamp:
                self.last_message_timestamp = userTimeStamp
                return userMessage
        return None
