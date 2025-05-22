import os
import pyodbc
from dotenv import load_dotenv
from opcua import Client
from products_ids import products
import datetime

class OPCUAClient:
    def __init__(
        self,
        url,
        products_dict,
        server: str,
        database: str,
        user: str,
        password: str,
        driver: str = "{ODBC Driver 17 for SQL Server}"
    ):
        self.url = url
        self.client = Client(url)
        self.products = products_dict
        self.conn_str = (
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password}"
        )
        self.setup_database()

    def connect(self):
        try:
            self.client.connect()
            return self.run()
        except Exception as e:
            print(f"Erro ao conectar ao OPC UA: {e}")
            return "As máquinas estão fora do ar, tente novamente mais tarde."

    def disconnect(self):
        self.client.disconnect()
        if hasattr(self, 'cnxn'):
            self.cnxn.close()

    def read_tag(self, node_id):
        try:
            return self.client.get_node(node_id).get_value()
        except Exception as e:
            print(f"Erro ao ler a tag {node_id}: {e}")
            return None

    def setup_database(self):
        self.cnxn = pyodbc.connect(self.conn_str, autocommit=False)
        self.cursor = self.cnxn.cursor()
        self.cursor.execute("""
            IF NOT EXISTS (
                SELECT * FROM sys.tables WHERE name = 'products'
            )
            CREATE TABLE products (
                machine_name NVARCHAR(100) PRIMARY KEY
            );
        """)
        self.cnxn.commit()

    def infer_sql_type(self, value):
        if isinstance(value, bool):
            return "BIT"
        if isinstance(value, int):
            return "INT"
        if isinstance(value, float):
            return "FLOAT"
        if isinstance(value, datetime.datetime):
            return "DATETIME2"
        length = max(50, len(str(value)))
        return f"NVARCHAR({length})"

    def ensure_columns(self, col_type_map):
        self.cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME='products'
        """)
        existing = {
            row.COLUMN_NAME: (row.DATA_TYPE, row.CHARACTER_MAXIMUM_LENGTH)
            for row in self.cursor.fetchall()
        }

        for col, sql_type in col_type_map.items():
            if col not in existing:
                self.cursor.execute(f"ALTER TABLE products ADD {col} {sql_type} NULL;")
            else:
                pass

        self.cnxn.commit()

    def save_data_to_db(self, machine_name, values: dict):
        try:
            col_names = [
                key.replace(" ", "_").replace("/", "_")
                for key in values.keys()
            ]
            col_type_map = {
                col: self.infer_sql_type(val)
                for col, val in zip(col_names, values.values())
            }
            self.ensure_columns(col_type_map)

            cols_str = ", ".join(col_names)
            placeholders = ", ".join("?" for _ in col_names)
            insert_sql = f"""
                INSERT INTO products (machine_name, {cols_str})
                VALUES (?, {placeholders})
            """
            params = [machine_name] + list(values.values())
            self.cursor.execute(insert_sql, params)
            self.cnxn.commit()

        except pyodbc.IntegrityError:
            try:
                set_clause = ", ".join(f"{col}=?" for col in col_names)
                update_sql = f"""
                    UPDATE products
                    SET {set_clause}
                    WHERE machine_name = ?
                """
                update_params = list(values.values()) + [machine_name]
                self.cursor.execute(update_sql, update_params)
                self.cnxn.commit()
            except Exception as e2:
                print(f"Erro no UPDATE: {e2}")
                self.cnxn.rollback()

        except Exception as e:
            print(f"Erro ao salvar dados no SQL Server: {e}")
            self.cnxn.rollback()

    def run(self):
        result = ""
        for machine_name, node_map in self.products.items():
            values = {}
            for node_id, tag_label in node_map.items():
                val = self.read_tag(node_id)
                if val is not None:
                    values[tag_label] = val
                    result += f"{machine_name} - {tag_label}: {val}\n"
            if values:
                self.save_data_to_db(machine_name, values)
        return result


if __name__ == "__main__":
    load_dotenv()

    opcua_client = OPCUAClient(
        url=os.getenv("OPCUA_IP"),
        products_dict=products,
        server=os.getenv("DB_SERVER"),
        database=os.getenv("DB_NAME_CONVERSATION"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    opcua_client.connect()
    opcua_client.disconnect()
