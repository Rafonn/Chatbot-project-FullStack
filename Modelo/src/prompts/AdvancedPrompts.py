# Importações adicionais
import os
import json
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain.chains import RetrievalQA
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

from machine_data.machineName import MachineInfoSQL
from product_data.productName import ProductInfoSQL
from index_data_for_rag import index_data_for_rag
from prompts.commands import commands
from machines.machines import machines_names

class AdvancedPrompts:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('API_KEY')
        os.environ["OPENAI_API_KEY"] = self.api_key # Define a variável de ambiente para LangChain
        
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        try:
            self.vectorstore = Chroma(persist_directory="./rag_db", embedding_function=self.embeddings)
            self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
            print("Vector database carregado com sucesso.")
        except Exception as e:
            print(f"Erro ao carregar vector database, tentando criar: {e}")
            self.vectorstore = index_data_for_rag()
            if self.vectorstore:
                self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
            else:
                print("Não foi possível inicializar o vector database. Funções RAG podem não funcionar.")
                self.retriever = None

        self._initialize_tools()
        self._initialize_agents()

    def _initialize_tools(self):
        self.tools = []

        if self.retriever:
            rag_qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.retriever,
                return_source_documents=True
            )
            self.tools.append(
                Tool(
                    name="data_retriever",
                    description="Útil para buscar informações detalhadas sobre máquinas, produtos ou qualquer outro dado indexado. Use para responder perguntas sobre características, status ou descrições.",
                    func=lambda query: rag_qa_chain.invoke({"query": query})['result']
                )
            )

        self.tools.append(
            Tool(
                name="get_machine_specific_info",
                description="Útil para obter informações específicas e diretas de uma máquina quando o nome exato da máquina é conhecido. Exemplo: 'me dê os detalhes da máquina Tear 01 - Jager TP100'.",
                func=self._get_machine_info_wrapper
            )
        )
        
        # Tool para identificar e buscar dados de Produto (ainda usando ProductInfoSQL para o exemplo)
        self.tools.append(
            Tool(
                name="get_product_specific_info",
                description="Útil para obter informações específicas e diretas de um produto quando o nome exato do produto é conhecido. Exemplo: 'qual o status do Pano XYZ'.",
                func=self._get_product_info_wrapper
            )
        )

        # Tool para lidar com o contexto "dude" (Ordem de Serviço)
        self.tools.append(
            Tool(
                name="dude_order_service_info",
                description="Use esta ferramenta quando o usuário perguntar sobre 'dude' ou 'ordem de serviço'. Esta ferramenta pode extrair datas, status e nomes de máquinas de uma consulta para buscar informações relacionadas a ordens de serviço. Exemplo: 'status da ordem de serviço CLT1 em 12/11/2023'.",
                func=self._dude_identify_wrapper # Encapusa a lógica existente
            )
        )

        self.tools.append(
            Tool(
                name="personalize_message",
                description="Útil para refazer uma mensagem de forma mais legal e divertida. Use quando for responder diretamente ao usuário e quiser que a resposta seja mais engajadora.",
                func=self._personalized_message
            )
        )

    def _get_machine_info_wrapper(self, query):
        machineName_identified_by_llm = self.llm.invoke(f"""
        O usuário quer informações sobre "{query}". Aqui estão as máquinas disponíveis:
        {machines_names}
        Qual dessas máquinas é a mais relevante? Responda APENAS com o nome exato da máquina mais parecida
        com a que o usuário informou. Se nenhuma for relevante, responda 'N/A'.
        """).content.strip()

        if machineName_identified_by_llm in machines_names:
            mi = MachineInfoSQL(machineName_identified_by_llm)
            info = mi.get_machine_info()
            return f"Informações sobre {machineName_identified_by_llm}:\n{info}"
        return "Não consegui identificar uma máquina específica na sua solicitação."

    def _get_product_info_wrapper(self, query):
        productName_identified_by_llm = self.llm.invoke(f"""
        O usuário quer informações sobre "{query}".
        Qual produto o usuário se refere? Responda APENAS com o nome exato do produto mais parecido
        com o que o usuário informou. Se nenhum for relevante, responda 'N/A'.
        """).content.strip()

        if "pano xyz" in productName_identified_by_llm.lower():
            pi = ProductInfoSQL("Pano XYZ")
            info = pi.get_product_info()
            return f"Informações sobre Pano XYZ:\n{info}"
        return "Não consegui identificar um produto específico na sua solicitação."

    def _dude_identify_wrapper(self, query):
        return json.dumps(self.dude_identify(query, machines_names))

    def _send_model(self, message):
        try:
            resp = self.llm.invoke(message)
            return resp.content
        except Exception as e:
            return f"Erro ao acessar a API: {e}"
    
    def _personalized_message(self, message):
        prompt = f"""
        Refaça a seguinte mensagem de forma legal e divertida, sem aspas:
        {message}
        """
        return self._send_model([{"role": "user", "content": prompt}])
    
    def dude_identify(self, message, machines):
        search_options = []

        date_prompt = f"""
        O user escreveu: "{message}"
        ANALISE BEM A MENSAGEM DO USUARIO.
        Há alguma data presente nessa mensagem? Se sim, responda com a data no formato ISO 8601 completo:  
        "YYYY-MM-DDThh:mm:ss" 
        Caso não haja data, responda com "vazio" sem aspas e sem pontuações.
        RESPONDA APENAS COM A DATA OU "vazio", SEM ASPAS E PONTUAÇÕES.
        """
        res = self._send_model([{"role": "user", "content": date_prompt}])
        search_options.append(res)

        status_prompt = f"""
        O user escreveu: "{message}"
        ANALISE BEM A MENSAGEM DO USUARIO.
        - Procurar as palavras parecidas com:  
            - Concluido → devolva "Completed" 
            - Em aberto → devolva "New Request"  
            - Em progresso → devolva "In Progress" 
        - Se nenhuma delas estiver presente, devolva "vazio" sem aspas e sem pontuações.

        RESPONDA APENAS COM "Completed", "New Request", "In Progress" ou "vazio" sem aspas e sem pontuações.
        """
        res = self._send_model([{"role": "user", "content": status_prompt}])
        search_options.append(res)

        machine_prompt = f"""
        O user escreveu: "{message}"
        ANALISE BEM A MENSAGEM DO USUARIO.
        - Se a mensagem contiver alguma palvra PARECIDA, podendo começar com a palavra ou não
          com um dos valores em: "{machines}", retornar esse valor. Por exemplo: "tear 1" -> "Tear 01 - Jager TP100"
        - Caso contrário, retornar "vazio".

        RESPONDA APENAS COM A PALAVRA OU "vazio" sem aspas e sem pontuações.
        """
        res = self._send_model([{"role": "user", "content": machine_prompt}])
        search_options.append(res)

        return search_options

    def _initialize_agents(self):
        
        main_agent_prompt = ChatPromptTemplate.from_messages([
            ("system", """Você é um assistente de IA multi-agente especializado em dados industriais e de negócios.
            Sua principal função é rotear as consultas para a ferramenta ou agente mais apropriado.
            Você tem acesso a ferramentas para:
            - Buscar informações gerais sobre máquinas e produtos (via RAG).
            - Obter detalhes específicos de máquinas quando o nome exato é conhecido.
            - Obter detalhes específicos de produtos quando o nome exato é conhecido.
            - Lidar com consultas relacionadas a 'ordens de serviço' ou 'dude', extraindo detalhes como datas, status e máquinas.
            - Personalizar suas mensagens para o usuário de forma divertida.

            Analise a intenção do usuário e utilize as ferramentas disponíveis de forma inteligente e sequencial, se necessário.
            Sempre forneça uma resposta completa e útil ao usuário.
            """),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])

        self.main_agent = create_openai_tools_agent(self.llm, self.tools, main_agent_prompt)
        self.main_agent_executor = AgentExecutor(
            agent=self.main_agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )

    def process_query(self, query: str, history: list = []):
        try:
            response = self.main_agent_executor.invoke({
                "input": query,
                "chat_history": history
            })
            return response["output"]
        except Exception as e:
            return f"Ocorreu um erro ao processar sua solicitação: {e}"

if __name__ == "__main__":

    prompts_instance = AdvancedPrompts()
    
    # Exemplo 1: Pergunta sobre máquina (via RAG)
    query1 = "Quais são as características da máquina de Tear 01?"
    print(f"\n--- Processando: '{query1}' ---")
    response1 = prompts_instance.process_query(query1)
    print("\n--- RESPOSTA FINAL 1 ---")
    print(response1)

    print("\n" + "="*80 + "\n")

    # Exemplo 2: Pergunta sobre ordem de serviço (via tool 'dude_order_service_info')
    query2 = "Quero saber sobre o processo no dude a partir do dia 12/11/2023 com status in progress, da máquina CLT1"
    print(f"\n--- Processando: '{query2}' ---")
    response2 = prompts_instance.process_query(query2)
    print("\n--- RESPOSTA FINAL 2 ---")
    print(response2)

    print("\n" + "="*80 + "\n")

    # Exemplo 3: Pergunta sobre produto (via RAG)
    query3 = "Me diga sobre as especificações do Pano XYZ."
    print(f"\n--- Processando: '{query3}' ---")
    response3 = prompts_instance.process_query(query3)
    print("\n--- RESPOSTA FINAL 3 ---")
    print(response3)
    
    print("\n" + "="*80 + "\n")

    # Exemplo 4: Pergunta ambígua ou que exige personalização
    query4 = "Olá, me diga algo sobre IA na saúde de forma divertida."
    print(f"\n--- Processando: '{query4}' ---")
    response4 = prompts_instance.process_query(query4)
    print("\n--- RESPOSTA FINAL 4 ---")
    print(response4)