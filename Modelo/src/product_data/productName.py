import os
import pyodbc
from dotenv import load_dotenv

nomes_personalizados = {
    "machine_name": "#### Equipamento",
    "Código_do_pano": "#### Código do pano",
    "Pano": "#### Pano",
    "Cliente": "#### Cliente",
    "Urdição": "#### Urdição",
    "Posição": "#### Posição",
    "Data_prometida": "#### Data prometida",
    "Picks": "#### Picks",
    "Metros_tecidos": "#### Metros tecidos",
    "Total_a_tecer": "#### Total a tecer",
    "Último_evento": "#### Último evento",
    "Observação": "#### Observação",
    "Data_de_início_de_tecimento": "#### Data de início de tecimento",
    "Hora_de_início_de_tecimento": "#### Hora de início de tecimento",
}

class ProductInfoSQL:
    def __init__(self, machine_name: str):
        load_dotenv()

        self.server   = os.getenv('DB_SERVER')
        self.database = os.getenv('DB_NAME_CONVERSATION')
        self.username = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.driver = "{ODBC Driver 17 for SQL Server}"

        self.conn_str = (
            f"DRIVER={self.driver};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
        )
        self.machine_name = machine_name

    def get_product_info(self) -> str:
        cnxn = pyodbc.connect(self.conn_str)
        cursor = cnxn.cursor()

        sql = "SELECT * FROM products WHERE machine_name = ?"
        cursor.execute(sql, (self.machine_name,))
        row = cursor.fetchone()
        if row is None:
            cursor.close()
            cnxn.close()
            return f"Equipamento '{self.machine_name}' não encontrado."

        column_names = [col[0] for col in cursor.description]

        cursor.close()
        cnxn.close()

        linhas = ["### STATUS DE TECIMENTO:"]
        for col, val in zip(column_names, row):
            nome_exibido = nomes_personalizados.get(col, col)
            if val == "00h:00m" or val == "Sem Informacao":
                val = "Sem informação"

            linhas.append(f"{nome_exibido}: {val}")

        return "\n".join(linhas)


if __name__ == "__main__":
    machine = ProductInfoSQL(
        machine_name="TP100 / Tear 01"
    )
    info = machine.get_machine_info()
    print(info)
