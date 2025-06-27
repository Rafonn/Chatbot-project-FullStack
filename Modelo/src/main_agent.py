import os
import json
import pyodbc
from dotenv import load_dotenv

from machines.formated_machines import formated_machines
from machines.machines import machines_names
from dude.filter import Filter
from cache.cache import ManualCachedEmbedder

from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.tools.retriever import create_retriever_tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.tools import tool
from langchain import hub
from typing import Optional
from thefuzz import process
from langchain.globals import set_llm_cache
from langchain_redis.cache import RedisCache

load_dotenv()

sql_server_config = {
    'driver': '{ODBC Driver 17 for SQL Server}', 
    'server': os.getenv("DB_SERVER_DEV"), 
    'database': os.getenv("DB_NAME_CONVERSATION"), 
    'uid': os.getenv("DB_USER_DEV"), 
    'pwd': os.getenv("DB_PASSWORD") 
}

@tool
def get_live_general_status() -> str:
    """Use esta ferramenta para obter o status em tempo real das maquinas e produtos. Quando não for informado uma máquina específica, retorna o status geral de todas as máquinas e produtos."""
        
    conn_str = (f"DRIVER={sql_server_config['driver']};SERVER={sql_server_config['server']};"
                f"DATABASE={sql_server_config['database']};UID={sql_server_config['uid']};"
                f"PWD={sql_server_config['pwd']};charset='UTF-8'")
    try:
        with pyodbc.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                query = """
                            SELECT * FROM products_status JOIN
                            machines_status ON products_status.machine_name = machines_status.machine_name;
                        """
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()

                if not rows:
                    return f"Nenhum dado encontrado'."
                
                data = [dict(zip(columns, row)) for row in rows]

                return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Ocorreu um erro ao conectar ao banco de dados: {e}"

@tool
def get_live_machine_status(machine_name_db: str) -> str:
    """Use esta ferramenta para obter o status em tempo real de uma máquina ou tear específico. Forneça o nome ou identificador da máquina."""

    canonical_equipment_name = None
    if machine_name_db:
        best_match, score = process.extractOne(machine_name_db, machines_names)
        print(best_match, score)
        if score >= 80:
            canonical_equipment_name = best_match
        else:
            return f"Equipamento '{machine_name_db}' não encontrado na lista de máquinas válidas."
        
    conn_str = (f"DRIVER={sql_server_config['driver']};SERVER={sql_server_config['server']};"
                f"DATABASE={sql_server_config['database']};UID={sql_server_config['uid']};"
                f"PWD={sql_server_config['pwd']};charset='UTF-8'")
    try:
        with pyodbc.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                query = "SELECT * FROM machines_status WHERE machine_name LIKE ?"
                cursor.execute(query, f'%{canonical_equipment_name}%')
                columns = [column[0] for column in cursor.description]
                row = cursor.fetchone()

                if not row:
                    return f"Nenhuma máquina encontrada com o nome parecido com '{canonical_equipment_name}'."
                
                data = dict(zip(columns, row))

                return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Ocorreu um erro ao conectar ao banco de dados: {e}"
    
@tool
def get_live_product_status(machine_name_db: str) -> str:
    """Use esta ferramenta para obter o status em tempo real de um PRODUTO específico. Forneça o nome ou identificador da máquina."""

    canonical_equipment_name = None
    if machine_name_db:
        best_match, score = process.extractOne(machine_name_db, machines_names)

        if score >= 80:
            canonical_equipment_name = best_match
        else:
            return f"Equipamento '{machine_name_db}' não encontrado na lista de máquinas válidas."
        
    conn_str = (f"DRIVER={sql_server_config['driver']};SERVER={sql_server_config['server']};"
                f"DATABASE={sql_server_config['database']};UID={sql_server_config['uid']};"
                f"PWD={sql_server_config['pwd']};charset='UTF-8'")
    try:
        with pyodbc.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                query = "SELECT * FROM products_status WHERE machine_name LIKE ?"
                cursor.execute(query, f'%{canonical_equipment_name}%')
                columns = [column[0] for column in cursor.description]
                row = cursor.fetchone()

                if not row:
                    return f"Nenhuma máquina encontrada com o nome parecido com '{canonical_equipment_name}'."
                
                data = dict(zip(columns, row))

                return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Ocorreu um erro ao conectar ao banco de dados: {e}"

@tool
def search_service_orders_api(user_input: str, equipment_name: Optional[str] = None, status: Optional[str] = None, date_iso: Optional[str] = None) -> str:
    """
    Busca ordens de serviço em uma API externa (Dude). Use sempre que o usuário perguntar sobre ordens de serviço, OS, ou chamados no Dude.
    - user_input: A entrada original do usuário, necessária para a classe Filter.
    - status: O status da ordem de serviço. Valores permitidos: 'New Request', 'Completed', 'In Progress'.
    - equipment_name: O nome do equipamento ou máquina a ser consultado.
    - date_iso: Estamos em 2025. A data da consulta no formato 'YYYY-MM-DDThh-mm-ss'. O agente pode converter 'hoje' ou 'ontem' para este formato.
    """
    print(f"--- ATIVANDO FERRAMENTA: search_service_orders_api ---")
    print(f"Parâmetros recebidos: Equipamento='{equipment_name}', Status='{status}', Data='{date_iso}'")
    
    canonical_equipment_name = None
    if equipment_name:
        best_match, score = process.extractOne(equipment_name, formated_machines)
        if score >= 80:
            canonical_equipment_name = best_match
    
    api_body_list = ["vazio", "vazio", "vazio"]

    if date_iso:
        api_body_list[0] = date_iso

    if status:
        api_body_list[1] = status

    if canonical_equipment_name:
        api_body_list[2] = canonical_equipment_name

    filter_instance = Filter(api_body_list, user_input)
    result = filter_instance.filter_order()

    return result

class IntelligentAssistant:
    def __init__(self, persist_directory="./rag_db_index"):

        load_dotenv()
        
        try:
            redis_url = "redis://localhost:6379/0"
            set_llm_cache(RedisCache(redis_url=redis_url))
        except Exception as e:
            print(f"AVISO: Cache de LLM com Redis desativado. Erro: {e}")

        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.tools = self._create_tools(persist_directory)

        prompt = hub.pull("hwchase17/openai-functions-agent")
        prompt.input_variables.append("chat_history")
        agent = create_openai_functions_agent(self.llm, self.tools, prompt)

        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)

    def _create_tools(self, persist_directory: str) -> list:

        base_embedder = OpenAIEmbeddings(model="text-embedding-3-small")
        cached_embedder = ManualCachedEmbedder(base_embedder=base_embedder)
        
        vectorstore = Chroma(
            persist_directory=persist_directory, 
            embedding_function=cached_embedder
        )
        retriever = vectorstore.as_retriever(search_kwargs={'k': 3})
        documentation_retriever_tool = create_retriever_tool(
            retriever,
            "documentation_search",
            "Use esta ferramenta para buscar informações sobre documentos, processos e procedimentos fixos da empresa..."
        )
        return [
            get_live_machine_status, 
            get_live_product_status, 
            search_service_orders_api, 
            get_live_general_status, 
            documentation_retriever_tool
        ]

    def run(self, user_input: str, chat_history: list) -> str:
        try:
            response = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": chat_history 
            })

            return response.get('output', "Não obtive uma resposta.")
        
        except Exception as e:
            return "Desculpe, enfrentei um problema técnico e não consegui processar sua solicitação."

    def start_chat(self):
        while True:
            user_input = input("Você: ")

            if user_input.lower() in ['sair', 'exit', 'quit']:
                print("Até logo!")
                break
            
            assistant_response = self.run(user_input)

            print(f"\nAssistente: {assistant_response}\n")

if __name__ == "__main__":
    assistant = IntelligentAssistant()
    assistant.start_chat()