import os
import pyodbc
from dotenv import load_dotenv

class SqlServerUserFetcher:
    def __init__(self):
        load_dotenv()

        self.server   = os.getenv('DB_SERVER')
        self.database = os.getenv('DB_NAME')
        self.username = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.table_name = "ActiveUsers"
        self.email_column = "UserEmail"
        self.active_column = "Active"
        self.driver = "{ODBC Driver 17 for SQL Server}"

    def _get_connection(self):
        conn_str = (
            f"DRIVER={self.driver};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password}"
        )
        return pyodbc.connect(conn_str)

    def get_user_ids(self) -> list:
        query = f"SELECT DISTINCT {self.email_column}, {self.active_column} FROM {self.table_name}"
        ids = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                ids = [row[0] for row in cursor.fetchall() if row[1] == 1]
        except pyodbc.Error as e:
            print(f"Erro ao acessar o banco: {e}")
        return ids

if __name__ == "__main__":
    fetcher = SqlServerUserFetcher()
    user_ids = fetcher.get_user_ids()
    print("IDs de usuários encontrados:", user_ids)
