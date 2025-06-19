from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json

from machine_data.machineName import MachineInfoSQL
from product_data.productName import ProductInfoSQL
from machines.machines import machines_names

def index_data_for_rag():
    print("Iniciando indexação de dados para RAG...")
    # Carregar dados de máquinas
    all_machines_data = []
    for machine_name in machines_names:
        mi_sql = MachineInfoSQL(machine_name)
        data = mi_sql.get_machine_info()
        if data:
            content = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else data
            all_machines_data.append(Document(page_content=content, metadata={"type": "machine", "name": machine_name}))
    
    all_products_data = []
    all_products_data.append(Document(page_content="Detalhes do produto 'Pano XYZ': Tipo Algodão, Gramatura 150g/m², Cor Azul, Produção diária 1000m.", metadata={"type": "product", "name": "Pano XYZ"}))
    all_products_data.append(Document(page_content="Detalhes do produto 'Tecido ABC': Material Poliéster, Uso Vestuário, Status: Em produção.", metadata={"type": "product", "name": "Tecido ABC"}))


    all_documents = all_machines_data + all_products_data
    
    if not all_documents:
        print("Nenhum dado encontrado para indexar.")
        return None

    # Fragmentação
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(all_documents)

    # Embeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Armazenamento no ChromaDB
    vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory="./rag_db")
    vectorstore.persist()
    print("Indexação concluída. Dados armazenados em ./rag_db")
    return vectorstore