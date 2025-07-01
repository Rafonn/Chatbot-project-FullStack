import os
import json
from dotenv import load_dotenv
from typing import List, TypedDict, Annotated
import operator

# Importações de Ferramentas e Agentes
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.tools.retriever import create_retriever_tool
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_openai_functions_agent

# --- NOVAS IMPORTAÇÕES PARA CHAINS SIMPLES ---
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Importações do LangGraph
from langgraph.graph import StateGraph, END

# --- Carregando Configurações ---
load_dotenv()

# --- Ferramentas ---
@tool
def search_internal_docs(query: str) -> str:
    """Busca na documentação interna da empresa (manuais, PDFs, procedimentos) para responder a uma pergunta."""
    print(f"--- Ferramenta Interna (RAG) ativada com a query: '{query}' ---")
    vectorstore = Chroma(persist_directory="./rag_db_index", embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"))
    retriever = vectorstore.as_retriever(search_kwargs={'k': 5}) # Aumentei k para mais contexto
    docs = retriever.invoke(query)
    if not docs:
        return "Nenhuma informação encontrada na documentação interna."
    return "\n\n".join([doc.page_content for doc in docs])

from langchain_google_community.search import GoogleSearchAPIWrapper, GoogleSearchRun
search_wrapper = GoogleSearchAPIWrapper()
web_search_tool = GoogleSearchRun(api_wrapper=search_wrapper)

# --- Definição do Estado do Agente ---
class AgentState(TypedDict):
    task: str
    plan: str
    draft: str
    review: str
    tool_output: Annotated[List[str], operator.add] 
    revision_number: int

# --- Definição dos Nós do Grafo ---
llm = ChatOpenAI(model="gpt-4o", temperature=0)

def plan_node(state: AgentState):
    """Nó de Planejamento: O supervisor cria um plano."""
    print("--- Nó: Planejador ---")
    system_prompt = "Você é o agente planejador. Sua tarefa é criar um plano passo a passo conciso para responder à solicitação do usuário. Descreva qual especialista deve agir: o 'pesquisador de documentação interna' ou o 'pesquisador web', ou ambos."
    
    # Usando uma chain simples: Prompt | LLM | Parser
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{task}")])
    planner_chain = prompt | llm | StrOutputParser()
    result = planner_chain.invoke({"task": state['task']})
    return {"plan": result}

def documentation_research_node(state: AgentState):
    """Nó de Pesquisa Interna: Executa a busca nos documentos RAG."""
    print("--- Nó: Pesquisador de Documentação ---")
    prompt = hub.pull("hwchase17/openai-functions-agent")
    system_prompt = "Você é um especialista em documentação interna da Andritz. Use a ferramenta de busca para encontrar a informação solicitada pelo usuário."
    agent = create_openai_functions_agent(llm, [search_internal_docs], prompt.partial(system_prompt=system_prompt))
    executor = AgentExecutor(agent=agent, tools=[search_internal_docs])
    result = executor.invoke({"input": state['task'], "chat_history": []})
    return {"tool_output": [f"Resultado da Pesquisa Interna:\n{result['output']}"]}

def web_search_node(state: AgentState):
    """Nó de Pesquisa Web: Executa a busca na internet."""
    print("--- Nó: Pesquisador Web ---")
    prompt = hub.pull("hwchase17/openai-functions-agent")
    system_prompt = "Você é um especialista em encontrar informações atualizadas e regulamentações na internet. Use a ferramenta de busca na web."
    agent = create_openai_functions_agent(llm, [web_search_tool], prompt.partial(system_prompt=system_prompt))
    executor = AgentExecutor(agent=agent, tools=[web_search_tool])
    result = executor.invoke({"input": state['task'], "chat_history": []})
    return {"tool_output": [f"Resultado da Pesquisa Web:\n{result['output']}"]}

def draft_node(state: AgentState):
    """Nó de Rascunho: Junta todas as informações em uma resposta coesa."""
    print("--- Nó: Redator ---")
    draft_input = f"Tarefa do Usuário: {state['task']}\n\nDados Coletados:\n" + "\n\n".join(state['tool_output'])
    system_prompt = "Você é um redator especialista. Com base na tarefa do usuário e nos dados coletados, escreva uma resposta final completa, consolidada e bem estruturada."

    # Usando uma chain simples para o redator também
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{draft_input}")])
    drafting_chain = prompt | llm | StrOutputParser()
    result = drafting_chain.invoke({"draft_input": draft_input})
    return {"draft": result}

# --- Lógica de Roteamento ---
def router(state: AgentState):
    """Decide qual nó executar a seguir com base no plano."""
    print("--- Nó: Roteador ---")
    plan = state['plan'].lower()
    if "pesquisador web" in plan and ("documentação interna" in plan or "documentos internos" in plan):
        print("Decisão: Chamar ambos os pesquisadores.")
        return ["doc_researcher", "web_searcher"]
    elif "pesquisador web" in plan:
        print("Decisão: Chamar Pesquisador Web.")
        return "web_searcher"
    elif "documentação interna" in plan or "documentos internos" in plan:
        print("Decisão: Chamar Pesquisador de Documentação.")
        return "doc_researcher"
    else:
        print("Decisão: Nenhum pesquisador necessário, seguir para a redação.")
        return "drafter"

# --- Construção do Grafo ---
workflow = StateGraph(AgentState)
workflow.add_node("planner", plan_node)
workflow.add_node("doc_researcher", documentation_research_node)
workflow.add_node("web_searcher", web_search_node)
workflow.add_node("drafter", draft_node)
workflow.set_entry_point("planner")
workflow.add_conditional_edges("planner", router, {"doc_researcher": "doc_researcher", "web_searcher": "web_searcher", "drafter": "drafter", "end": END})
workflow.add_edge("doc_researcher", "drafter")
workflow.add_edge("web_searcher", "drafter")
workflow.add_edge("drafter", END)
app = workflow.compile()

# --- Execução ---
if __name__ == "__main__":
    task = "Com base na FISPQ da aguarrás que temos internamente, quais são os EPIs recomendados? E pesquise na web se a OSHA tem recomendações adicionais."
    
    print(f"Iniciando tarefa complexa: {task}\n" + "="*50)
    
    for s in app.stream({"task": task, "revision_number": 0, "tool_output": []}):
        # Imprime o nome do nó e seu resultado a cada passo
        node_name = list(s.keys())[0]
        node_output = list(s.values())[0]
        print(f"### SAÍDA DO NÓ: {node_name} ###")
        print(node_output)
        print("----")