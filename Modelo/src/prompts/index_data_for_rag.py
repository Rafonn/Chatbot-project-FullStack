import os
import json
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import pyodbc

class RAGIndexer:
    def __init__(self, persist_directory: str = "./rag_db", 
                 embedding_model: str = "text-embedding-3-small",
                 chunk_size: int = 1000, 
                 chunk_overlap: int = 100,
                 db_config: dict = None):
        
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.db_config = db_config 
        print(f"RAGIndexer inicializado com persist_directory='{self.persist_directory}' e modelo de embedding='{embedding_model}'.")

    def _get_db_connection(self):
        # (Esta função está correta, sem alterações)
        if not self.db_config:
            print("Erro: Configuração do banco de dados não fornecida.")
            return None
        
        conn_str = (
            f"DRIVER={self.db_config['driver']};"
            f"SERVER={self.db_config['server']};"
            f"DATABASE={self.db_config['database']};"
            f"UID={self.db_config['uid']};"
            f"PWD={self.db_config['pwd']};"
            "charset='UTF-8'"
        )
        try:
            conn = pyodbc.connect(conn_str)
            print("Conexão com o SQL Server estabelecida com sucesso!")
            return conn
        except pyodbc.Error as ex:
            sqlstate = ex.args[0]
            print(f"Erro ao conectar ao SQL Server: {sqlstate} - {ex}")
            return None

    # --- FUNÇÃO QUE ESTAVA FALTANDO ---
    # Esta função é necessária para as tabelas 'machines_status' e 'products'
    def _extract_content_and_metadata(self, row_data: dict, table_name: str, name_column: str = None, doc_type: str = None) -> Document:
        metadata = {"source_table": table_name}
        if 'id' in row_data:
            metadata['id'] = row_data['id']
        if name_column and name_column in row_data:
            metadata['name'] = row_data[name_column]
        if doc_type:
            metadata['type'] = doc_type

        def clean_value(value):
            if value is None:
                return ""
            return str(value).strip()

        clean_row_data = {k: clean_value(v) for k, v in row_data.items()}
        content_for_page = json.dumps(clean_row_data, ensure_ascii=False, indent=2)
        return Document(page_content=content_for_page, metadata=metadata)
        
    def _load_data_from_sql(self, table_name: str, name_column: str = None, doc_type: str = None) -> list[Document]:
        # (Esta função estava chamando a função que faltava, agora vai funcionar)
        documents = []
        conn = None
        try:
            conn = self._get_db_connection()
            if not conn:
                return [] 

            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}") 
            columns = [column[0] for column in cursor.description] 

            print(f"Buscando dados da tabela '{table_name}' (método SQL padrão)...")
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                # ESTA LINHA AGORA FUNCIONA
                doc = self._extract_content_and_metadata(row_dict, table_name, name_column, doc_type)
                documents.append(doc)
            
            print(f"Coletados {len(documents)} documentos da tabela '{table_name}'.")
        except Exception as e:
            print(f"Erro ao processar dados da tabela '{table_name}': {e}")
        finally:
            if conn:
                conn.close()
        return documents

    def _load_docs_from_json_column(self, table_name: str, content_column: str = 'file_content', metadata_columns: list = ['id', 'file_name']) -> list[Document]:
        # (Esta função está correta, sem alterações)
        documents = []
        conn = None
        try:
            conn = self._get_db_connection()
            if not conn:
                return []
            columns_to_select = ", ".join(metadata_columns + [content_column])
            cursor = conn.cursor()
            cursor.execute(f"SELECT {columns_to_select} FROM {table_name}")
            print(f"Buscando e processando documentos da tabela '{table_name}' (formato JSON em coluna)...")
            cols = [column[0] for column in cursor.description]
            for row in cursor.fetchall():
                row_dict = dict(zip(cols, row))
                json_string = row_dict.get(content_column)
                if not json_string:
                    continue
                try:
                    data = json.loads(json_string)
                    page_content = "\n\n".join(str(value).strip() for value in data.values())
                    metadata = {"source_table": table_name}
                    for col in metadata_columns:
                        if col in row_dict:
                            metadata[col] = row_dict[col]
                    doc = Document(page_content=page_content, metadata=metadata)
                    documents.append(doc)
                except json.JSONDecodeError as e:
                    print(f"Erro ao decodificar JSON na linha com id={row_dict.get('id', 'N/A')}: {e}")
            print(f"Coletados e processados {len(documents)} documentos da tabela '{table_name}'.")
        except Exception as e:
            print(f"Erro ao processar a tabela '{table_name}': {e}")
        finally:
            if conn:
                conn.close()
        return documents
    
    def index_data(self):
        print("\nIniciando indexação de dados para RAG...")
        all_documents = []

        # Indexando tabelas com estrutura padrão
        all_documents.extend(self._load_data_from_sql(table_name="machines_status", name_column="machine_name", doc_type="machine"))
        # CORREÇÃO: Usando a coluna de nome correta para produtos
        all_documents.extend(self._load_data_from_sql(table_name="products", name_column="product_name", doc_type="product"))

        # Indexando tabelas com a estrutura de JSON em coluna
        all_documents.extend(self._load_docs_from_json_column(table_name="tecelagem_e_revisao"))
        all_documents.extend(self._load_docs_from_json_column(table_name="mantas"))
        all_documents.extend(self._load_docs_from_json_column(table_name="recepcao_de_materiais"))
        all_documents.extend(self._load_docs_from_json_column(table_name="preparacao_de_fios"))
        all_documents.extend(self._load_docs_from_json_column(table_name="pean_sean_felts_PSF"))
        all_documents.extend(self._load_docs_from_json_column(table_name="metrologia"))
        all_documents.extend(self._load_docs_from_json_column(table_name="expedicao"))
        all_documents.extend(self._load_docs_from_json_column(table_name="acabamento"))
        
        if not all_documents:
            print("Nenhum dado encontrado para indexar. Indexação abortada.")
            return None

        print(f"\nFragmentando {len(all_documents)} documentos...")
        chunks = self.text_splitter.split_documents(all_documents)
        print(f"Total de fragmentos gerados: {len(chunks)}")

        print(f"Gerando embeddings e armazenando no ChromaDB em '{self.persist_directory}'...")
        try:
            vectorstore = Chroma.from_documents(
                documents=chunks, 
                embedding=self.embeddings, 
                persist_directory=self.persist_directory
            )
            print("Indexação concluída. Dados armazenados com sucesso!")
            return vectorstore
        except Exception as e:
            print(f"Erro durante a indexação ou persistência no ChromaDB: {e}")
            return None

if __name__ == "__main__":
    load_dotenv()

    sql_server_config = {
        'driver': '{ODBC Driver 17 for SQL Server}', 
        'server': os.getenv("DB_SERVER_DEV"), 
        'database': os.getenv("DB_NAME_CONVERSATION"), 
        'uid': os.getenv("DB_USER_DEV"), 
        'pwd': os.getenv("DB_PASSWORD") 
    }
    
    # Apagar a pasta ./my_rag_db_index para reindexar tudo com o código corrigido.

    indexer = RAGIndexer(
        persist_directory="./my_rag_db_index",
        embedding_model="text-embedding-3-small",
        db_config=sql_server_config 
    )

    vector_db = indexer.index_data()

    if vector_db:
        query_machine = "qual o status do 1015?"
        
        retriever = vector_db.as_retriever(
            search_kwargs={
                'k': 1,
                'filter': {'source_table': 'machines_status'}
            }
        )

        # Usamos o retriever para buscar os documentos.
        docs = retriever.invoke(query_machine)
        
        full_response_content = f"\n--- Conteúdo da busca para '{query_machine}' (FILTRADO por Tabela: machines_status) ---\n"
        
        if not docs:
            full_response_content += "Nenhum documento relevante encontrado na tabela 'machines_status'."
        else:
            for i, doc in enumerate(docs):
                source_table = doc.metadata.get('source_table', 'N/A')
                # Agora vamos procurar pelo 'name' da máquina, que definimos no _extract_content_and_metadata
                machine_name = doc.metadata.get('name', 'N/A')
                doc_id = doc.metadata.get('id', 'N/A')
                
                full_response_content += f"\n--- Documento Relevante {i+1} (Fonte: {source_table}, ID: {doc_id}, Máquina: {machine_name}) ---\n"
                full_response_content += doc.page_content + "\n"
        
        print(full_response_content)

    else:
        print("\nNão foi possível criar ou carregar o VectorStore.")