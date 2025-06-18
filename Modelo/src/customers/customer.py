import os
import pyodbc
from dotenv import load_dotenv

class Customer:
    def __init__(self):
        load_dotenv()

        self.server   = os.getenv('DB_SERVER_DEV')
        self.database = os.getenv('DB_NAME')
        self.username = os.getenv('DB_USER_DEV')
        self.password = os.getenv('DB_PASSWORD')

        self.conn_str = (
            'DRIVER={ODBC Driver 17 for SQL Server};'
            f'SERVER={self.server};'
            f'DATABASE={self.database};'
            f'UID={self.username};'
            f'PWD={self.password};'
            'TrustServerCertificate=yes;'
        )
    
    def fetch_customer(self, customer):
        with pyodbc.connect(self.conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT A.OID_Cliente, A.CodCli, A.Marca, B.Nome AS Pais
                FROM MKT_Cliente A
                INNER JOIN MKT_Pais B ON B.OID_Pais = A.OID_Pais
                WHERE A.StatusQualidCli = 'A'
                AND A.Marca LIKE '%{customer}%';
            """)

        return cursor.fetchall()

    def fetch_product(self, customer):
        with pyodbc.connect(self.conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT E.Marca, A.Produto, A.IdPosicao, A.Comprimento, A.Largura, A.Gramatura, A.Units, A.DataSolicitada, A.DataPrometida, B.Descricao, D.Descricao AS Fase
                FROM MKT_Pedido A
                INNER JOIN MKT_DescricaoComercial B ON B.OID_DescricaoComercial = A.OID_DescricaoComercial
                LEFT JOIN MFT_StatusProduto C ON C.OID_Pedido = A.OID_Pedido
                LEFT JOIN MFT_FasesProducao D ON D.OID_Fase = C.OID_Fase
                INNER JOIN MKT_CLiente E ON E.OID_Cliente = A.OID_Cliente
                WHERE E.Marca like '%{customer}%' AND A.Classe IN ('FA', 'TI') AND A.StatusPedido='A'
            """)

        return cursor.fetchall()