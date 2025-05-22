import os
import openai
import traceback
import time
import threading
from multiprocessing import Process, set_start_method
from dotenv import load_dotenv

from db_logs.receive import LastMessageFetcher
from db_logs.toggleReceive import ToggleButtonStatus
from user_conversation.conversation import Conversation
from helpers.users import SqlServerUserFetcher
from helpers.context import Context
from machines.machines import machines_names
from prompts.prompts import Prompts
from prompts.prompts import commands
from dude.formated_machines import formated_machines
from dude.filter import Filter

class RestartException(Exception):
    pass

class ChatAndritz:
    def __init__(self, user_id):
        self.user_id = user_id

        self.message_fetcher = LastMessageFetcher(self.user_id)

        self.receive_toggle = ToggleButtonStatus(self.user_id)

        self.history = [{"role": "system", "content": commands["initial"]}]

        self.verify_state = self._verify_input()
        self.restart_flag = threading.Event()
        self.monitor_thread = threading.Thread(target=self._monitor_input, daemon=True)
        self.monitor_thread.start()
    
    def _monitor_input(self):
        while True:
            current = self._verify_input()
            if current != self.verify_state:
                self.verify_state = current
                self.restart_flag.set()
            time.sleep(0.1)

    def _check_restart(self):
        if self.restart_flag.is_set():
            self._log_and_print("⚠️ Mudança detectada! Reiniciando verificações...")
            return True
        return False

    def _log_and_print(self, message):
        conv = Conversation(message, self.user_id)
        conv.botResponse()

    def _verify_input(self):
        key = ToggleButtonStatus(self.user_id)
        return key.fetch_status()

    def _listar_tabelas(self):
        tabel = Context()
        return tabel.listar_tabelas_sql_server()
    
    def _consultar_tabela(self, nome_tabela):
        data = Context()
        return data.consultar_tabela(nome_tabela)

    def _escolher_maquina(self, user):
        machine = Prompts()
        self._log_and_print(machine.machine_identify(user))
    
    def _escolher_produto(self, user):
        product = Prompts()
        self._log_and_print(product.product_identify(user))
    
    def _dude(self, user):
        dude_options = Prompts()
        dude = dude_options.dude_identify(user, formated_machines)
        
        filter = Filter(dude, user)
        self._log_and_print(filter.filter_order())
    
    def _identificar_contexto(self, user_input):
        tabelas = self._listar_tabelas()
        context = Prompts()

        escolha = context.context_identify(user_input, tabelas, machines_names)
        print(f"Escolha: {escolha}")
        if escolha in tabelas and escolha.lower() != "machine":
            dados = self._consultar_tabela(escolha)

            if not dados:
                self._log_and_print("A tabela está vazia.")
                return
            
            table = Prompts()
            self._log_and_print(table.table_identidy(dados, escolha))

        elif escolha.lower() == "machine":
            self._escolher_maquina(user_input)
        elif escolha.lower() == "produto":
            self._escolher_produto(user_input)
        elif escolha.lower() == "dude":
            self._dude(user_input)
        else:
            self._log_and_print("Não identifiquei tabela. Pode tentar de novo?")
    
    def _esperar_entrada_usuario(self):
        while not self.restart_flag.is_set():
            nova = self.message_fetcher.fetch_last_message()
            if nova:
                return nova

            time.sleep(0.5)

    def chat(self):
        while True:
            try:
                while True:
                    if self.restart_flag.is_set():
                        raise RestartException()

                    if self._verify_input():
                        user = self._esperar_entrada_usuario()
                        self._identificar_contexto(user)
                    else:
                        user = self._esperar_entrada_usuario()
                        response = Prompts()
                        bot_response = response.default_prompt(self.history, user)
                        self.history.append({"role": "user", "content": user})
                        self.history.append({"role": "assistant", "content": bot_response})
                        self._log_and_print(bot_response)
            except RestartException:
                self._log_and_print("⚠️ Mudança detectada! Reiniciando verificações...")
                self.restart_flag.clear()

def start_chat_for_user(user_id, empty = ""):
    try:
        bot = ChatAndritz(user_id=user_id)
    except Exception:
        traceback.print_exc()
        return

    try:
        bot.chat()
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    try:
        set_start_method('spawn')
    except RuntimeError:
        pass

    users = SqlServerUserFetcher()

    active_processes = {}
    POLL_INTERVAL = 60

    while True:
        current_ids = set(users.get_user_ids())
        running_ids = set(active_processes.keys())

        for uid in (current_ids - running_ids):
            p = Process(
                target=start_chat_for_user,
                args=(uid, ""),
                name=f"ChatAndritz-{uid}"
            )
            p.daemon = True
            p.start()
            active_processes[uid] = p

        for uid, p in list(active_processes.items()):
            if not p.is_alive():
                active_processes.pop(uid)

        time.sleep(POLL_INTERVAL)