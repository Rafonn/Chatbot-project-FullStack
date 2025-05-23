import os
import openai
import json
from dotenv import load_dotenv
from prompts.commands import commands
from machines.machines import machines_names
from machine_data.machineName import MachineInfoSQL
from product_data.productName import ProductInfoSQL

class Prompts:
    def __init__(self):
        load_dotenv()

        self.api_key = os.getenv('API_KEY')
        openai.api_key = self.api_key

    def _send_model(self, message):
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=message,
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"Erro ao acessar a API: {e}"
    
    def default_prompt(self, history, message):
        response = self._send_model(history + [{"role": "user", "content": message}])

        return response
    
    def _personalized_message(self, message):
        prompt = f"""
        Refaça a seguinte mensagem de forma legal e divertida, sem aspas:
        {message}
        """
        return self._send_model([{"role": "user", "content": prompt}])
    
    def context_identify(self, message, tabelas, maquinas):
        prompt = f"""
            O usuário enviou: "{message}".
            Se a mensagem contiver e APENAS SE CONTIVER uma dessas palavra como "dude" ou "ordem de serviço", 
            PODENDO AS PALAVRAS SEREM NO PLURAL OU SINGULAR,
            responda com "dude". Senão, responda com "vazio". ANALISE BEM A PALVRA E A LOGICA QUE VOCE IRA USAR. OBS:
            Responda APENAS com "vazio" ou "dude". Sem aspas, pontuações e tudo em minusculo.
        """

        res = self._send_model([{"role": "user", "content": prompt}])

        if(res.lower() == "vazio"):
            prompt = f"""
                O usuário enviou a seguinte mensagem: {message}
                Se a mensagem contiver alguma palavra como: "produto", "pano", "cliente", podendo ser plural ou singular, responda "produto".
                A palavra deve ser identificada baseada
                no contexto do usuário. Por isso, caso ele escreva "tecelagem", a resposta seria "vazio", pois ele quer saber
                sobre a tecelagem e não sobre o produto em si.
                Senão, responda com "vazio". ANALISE BEM A PALVRA E PENSE NA LOGICA QUE VOCE IRA USAR. OBS:
                Responda APENAS com "vazio" ou "machine". Sem aspas, pontuações e tudo em minusculo.
            """
            res = self._send_model([{"role": "user", "content": prompt}])

        if(res == "vazio"):
            prompt = f"""
                O usuário enviou a seguinte mensagem: {message}
                Se a mensagem contiver alguma chave: {maquinas}, responda "machine". A palavra deve ser identificada baseada
                no contexto do usuário. Por isso, caso ele escreva "tecelagem", a resposta seria "vazio", pois ele quer saber
                sobre a tecelagem e não sobre a máquina em si.
                Senão, responda com "vazio". ANALISE BEM A PALVRA E PENSE NA LOGICA QUE VOCE IRA USAR. OBS:
                Responda APENAS com "vazio" ou "machine". Sem aspas, pontuações e tudo em minusculo.
            """
            res = self._send_model([{"role": "user", "content": prompt}])

        if (res.lower() == "vazio"):
            prompt = f"""
                O usuário enviou: "{message}".
                Tabelas disponíveis: {tabelas}
                Qual tabela ele quer consultar? Responda só com o nome exato da tabela (ou "vazio").
            """
            res = self._send_model([{"role": "user", "content": prompt}])
        
        return res
    
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

    def machine_identify(self, message):
        prompt = f"""
        O usuário quer informações sobre "{message}". Aqui estão as máquinas disponíveis:
        {machines_names}
        Qual dessas máquinas é a mais relevante? Responda APENAS com o nome exato da máquina mais parecida
        com a que o usuário informou.
        """
        machineName = self._send_model([{"role": "user", "content": prompt}])

        if machineName in machines_names:
            mi = MachineInfoSQL(machineName)
            info = mi.get_machine_info()
            bot_msg = f"Ótima escolha! Buscando informações sobre '{machineName}'..."
            bot_msg = self._personalized_message(bot_msg)
            return f"{bot_msg}\n{info}"
        
    def product_identify(self, message):
        prompt = f"""
        O usuário quer informações sobre "{message}". Aqui estão as máquinas disponíveis:
        {machines_names}
        Qual dessas máquinas é a mais relevante? Responda APENAS com o nome exato da máquina mais parecida
        com a que o usuário informou.
        """
        machineName = self._send_model([{"role": "user", "content": prompt}])

        if machineName in machines_names:
            mi = ProductInfoSQL(machineName)
            info = mi.get_product_info()
            bot_msg = f"Ótima escolha! Buscando informações sobre '{machineName}'..."
            bot_msg = self._personalized_message(bot_msg)
            return f"{bot_msg}\n{info}"
        
    def table_identidy(self, data, choice):
        prompt = f"""
            Gere uma resposta amigável com os dados da tabela '{choice}':
            {json.dumps(data, indent=2, ensure_ascii=False)}
            """
        
        resp = self._send_model([{"role": "user", "content": prompt}])

        return resp

if __name__ == "__main__":
    sla = Prompts()
    prompt = "quero saber sobre o processo no dude a partir do dia 12/11/23 com status in progress, da maquina clt1"
    print(sla.dude_identify(prompt, {"CLT1", "Tear 01"}))