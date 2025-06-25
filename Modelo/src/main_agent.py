import os
import json
import pyodbc
from dotenv import load_dotenv
from datetime import datetime, timedelta

from machines.formated_machines import formated_machines
from dude.filter import Filter

from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.tools.retriever import create_retriever_tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.tools import tool
from langchain import hub
from langchain_core.messages import AIMessage, HumanMessage
from typing import Optional
from thefuzz import process

load_dotenv()

sql_server_config = {
    'driver': '{ODBC Driver 17 for SQL Server}', 
    'server': os.getenv("DB_SERVER_DEV"), 
    'database': os.getenv("DB_NAME_CONVERSATION"), 
    'uid': os.getenv("DB_USER_DEV"), 
    'pwd': os.getenv("DB_PASSWORD") 
}

@tool
def get_live_machine_status(machine_name: str) -> str:
    """Use esta ferramenta para obter o status em tempo real de uma máquina ou tear específico. Forneça o nome ou identificador da máquina."""

    conn_str = (f"DRIVER={sql_server_config['driver']};SERVER={sql_server_config['server']};"
                f"DATABASE={sql_server_config['database']};UID={sql_server_config['uid']};"
                f"PWD={sql_server_config['pwd']};charset='UTF-8'")
    try:
        with pyodbc.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                query = "SELECT * FROM machines_status WHERE machine_name LIKE ?"
                cursor.execute(query, f'%{machine_name}%')
                columns = [column[0] for column in cursor.description]
                row = cursor.fetchone()

                if not row:
                    return f"Nenhuma máquina encontrada com o nome parecido com '{machine_name}'."
                
                data = dict(zip(columns, row))

                return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Ocorreu um erro ao conectar ao banco de dados: {e}"

@tool
def search_service_orders_api(user_input: str, equipment_name: Optional[str] = None, status: Optional[str] = None, date_iso: Optional[str] = None) -> str:
    """
    Busca ordens de serviço em uma API externa (Dude). Use sempre que o usuário perguntar sobre ordens de serviço, OS, ou chamados no Dude.
    - user_input: A entrada original do usuário, necessária para a classe Filter.
    - equipment_name: O nome do equipamento ou máquina a ser consultado.
    - status: O status da ordem de serviço. Valores permitidos: 'New Request', 'Completed', 'In Progress'.
    - date_iso: A data da consulta no formato 'YYYY-MM-DD'. O agente pode converter 'hoje' ou 'ontem' para este formato.
    """
    print(f"--- ATIVANDO FERRAMENTA: search_service_orders_api ---")
    print(f"Parâmetros recebidos: Equipamento='{equipment_name}', Status='{status}', Data='{date_iso}'")
    
    canonical_equipment_name = None
    if equipment_name:
        best_match, score = process.extractOne(equipment_name, formated_machines)

        if score >= 80:
            canonical_equipment_name = best_match
        else:
            return f"Equipamento '{equipment_name}' não encontrado na lista de máquinas válidas."
    
    api_body_list = ["vazio", "vazio", "vazio"]

    if date_iso:
        try:
            parsed_date = datetime.fromisoformat(date_iso.replace("Z", "+00:00"))
            api_body_list[0] = parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            api_body_list[0] = date_iso

    if canonical_equipment_name:
        api_body_list[1] = canonical_equipment_name

    if status:
        api_body_list[2] = status

    if all(v == "vazio" for v in api_body_list):
        return "Por favor, para buscar uma ordem de serviço, especifique pelo menos um critério."

    filter_instance = Filter(api_body_list, user_input)
    result = filter_instance.filter_order()

    return result

class IntelligentAssistant:
    def __init__(self, persist_directory="./my_rag_db_index"):
        print("Inicializando o Assistente Inteligente...")

        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.tools = self._create_tools(persist_directory)

        prompt = hub.pull("hwchase17/openai-functions-agent")
        prompt.input_variables.append("chat_history")
        agent = create_openai_functions_agent(self.llm, self.tools, prompt)

        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        
        print("Assistente pronto!")

    def _create_tools(self, persist_directory: str) -> list:
        vectorstore = Chroma(
            persist_directory=persist_directory, 
            embedding_function=OpenAIEmbeddings(model="text-embedding-3-small")
        )

        retriever = vectorstore.as_retriever(search_kwargs={'k': 3})

        documentation_retriever_tool = create_retriever_tool(
            retriever, "documentation_search", "Use esta ferramenta para buscar informações sobre documentos, processos e procedimentos fixos da empresa...")
        
        return [get_live_machine_status, search_service_orders_api, documentation_retriever_tool]

    def run(self, user_input: str, chat_history: list) -> str:
        try:
            response = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": chat_history 
            })

            return response.get('output', "Não obtive uma resposta.")
        
        except Exception as e:
            print(f"\nOcorreu um erro inesperado durante a execução do agente: {e}")
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