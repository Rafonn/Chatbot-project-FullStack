import os
import pyodbc
from dotenv import load_dotenv

nomes_personalizados = {
    "machine_name": "#### Equipamento",
    "Parado___Rodando": "#### Parado / Rodando",
    "Tempo_parado_atual": "#### Tempo parado atual",
    "Ultimo_tempo_parado": "#### Último tempo parado",
    "Tempo_parado_do_dia": "#### Tempo parado do dia",
    "Tempo_parado_do_dia_anterior": "#### Tempo parado do dia anterior",
    "Tempo_parado_na_semana_anterior": "#### Tempo parado na semana anterior",
    "Eficiencia_atual": "#### Eficiência",
    "Batidas": "#### Batidas do dia",
}

class MachineInfoSQL:
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

    def get_machine_info(self) -> str:
        cnxn = pyodbc.connect(self.conn_str)
        cursor = cnxn.cursor()

        sql = "SELECT * FROM machines WHERE machine_name = ?"
        cursor.execute(sql, (self.machine_name,))
        row = cursor.fetchone()
        if row is None:
            cursor.close()
            cnxn.close()
            return f"Equipamento '{self.machine_name}' não encontrado."

        column_names = [col[0] for col in cursor.description]

        cursor.close()
        cnxn.close()

        linhas = ["### STATUS:"]
        for col, val in zip(column_names, row):
            nome_exibido = nomes_personalizados.get(col, col)
            if col == "Parado___Rodando":
                if val == 0:
                    val = "Parado"
                elif val == 1:
                    val = "Rodando"
            
            if col == "Eficiencia_atual":
                val = f"{round(val, 1)} %"

            linhas.append(f"{nome_exibido}: {val}")

        return "\n".join(linhas)


if __name__ == "__main__":
    machine = MachineInfoSQL(
        machine_name="CLT1"
    )
    info = machine.get_machine_info()
    print(info)
