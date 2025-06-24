import os
import openai
import json
from dotenv import load_dotenv
from machines.machines import machines_names
from index_data_for_rag import RAGIndexer

class AdvancedPrompts:
    def __init__(self):
        load_dotenv()

    def _send_model(self, message):
        try:
            resp = openai.chat.completions.create(
                model="gpt-4o",
                messages=message,
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"Erro ao acessar a API: {e}"
        
    def default_prompt(self, history, message):
        response = self._send_model(history + [{"role": "user", "content": message}])

        return response
    
    def api_identify(self, message):
        prompt = f"""
            O usuário enviou: "{message}".
            Se a mensagem contiver e APENAS SE CONTIVER uma dessas palavra como "dude" ou "ordem de serviço", 
            PODENDO AS PALAVRAS SEREM NO PLURAL OU SINGULAR,
            responda com "dude". Senão, responda com "vazio". ANALISE BEM A PALVRA E A LOGICA QUE VOCE IRA USAR. OBS:
            Responda APENAS com "vazio" ou "dude". Sem aspas, pontuações e tudo em minusculo.
        """

        res = self._send_model([{"role": "user", "content": prompt}])

        if(res.lower() == "dude"): return True
        
        return False

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

    def filter_order(self, dude, user):
        return f"{user}, você filtrou o pedido com base no Dude: {dude}."

    def costumer_identify(self, user):
        return f"{user}, você escolheu a opção de Cliente."

    def costumer_product_identify(self, user):
        return f"{user}, você escolheu a opção de Produto do Cliente."