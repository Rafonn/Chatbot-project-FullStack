import traceback
import time
from multiprocessing import Process, set_start_method

from main_agent import IntelligentAssistant
from db_logs.receive import LastMessageFetcher
from user_conversation.conversation import Conversation
from helpers.users import SqlServerUserFetcher

from langchain_core.messages import AIMessage, HumanMessage

class ChatAndritz:
    def __init__(self, user_id):
        self.user_id = user_id
        self.message_fetcher = LastMessageFetcher(self.user_id)
        self.assistant = IntelligentAssistant()
        self.chat_history = []

    def _log_and_print(self, message):
        if not message: return
        
        conv = Conversation(message, self.user_id)
        conv.botResponse()
    
    def _esperar_entrada_usuario(self):
        while True:
            nova_mensagem = self.message_fetcher.fetch_last_message()
            if nova_mensagem: return nova_mensagem
            time.sleep(0.5)

    def chat(self):

        while True:
            user_message = self._esperar_entrada_usuario()
            bot_response = self.assistant.run(user_message, self.chat_history)
    
            self.chat_history.append(HumanMessage(content=user_message))
            self.chat_history.append(AIMessage(content=bot_response))
            
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]

            print(f"[{self.user_id}] Resposta do Bot: '{bot_response}'")
            self._log_and_print(bot_response)

def start_chat_for_user(user_id):
    try:
        bot = ChatAndritz(user_id=user_id)
        bot.chat()
    except Exception:
        print(f"O processo para o usuário {user_id} encontrou um erro fatal.")
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
        try:
            current_ids = set(users.get_user_ids())
            running_ids = set(active_processes.keys())

            for uid in (current_ids - running_ids):
                print(f"Novo usuário detectado: {uid}. Iniciando processo de chat.")
                
                p = Process(
                    target=start_chat_for_user,
                    args=(uid,),
                    name=f"ChatAndritz-{uid}"
                )
                p.daemon = True
                p.start()
                active_processes[uid] = p

            for uid, p in list(active_processes.items()):
                if not p.is_alive():
                    active_processes.pop(uid)

            time.sleep(POLL_INTERVAL)

        except Exception as e:
            print(f"Erro no loop principal do gerenciador de processos: {e}")
            traceback.print_exc()
            time.sleep(POLL_INTERVAL)