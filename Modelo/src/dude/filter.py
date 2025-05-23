from dude.dude import DudeSolutions

class Filter:

    def __init__(self, bot_message, user_message):
        self.bot_message = bot_message
        self.user_message = user_message

        print(bot_message)
        print(user_message)

    def filter_order(self):
        filter = DudeSolutions(self.bot_message[0], self.bot_message[1])
        filtered = filter.getOrderBy()

        filtered_by_machine = self._filter_by_machine(filtered)

        return filtered_by_machine


    def _filter_by_machine(self, orders):
        machine_code = self.bot_message[2]
        print(f"Maquina: {self.bot_message[2]}")

        by_name = [order for order in orders if self._filter_by_name(order)]

        if machine_code.lower() == 'vazio':
            result = by_name if by_name else orders
            return self._format_to_string(result)

        base_list = by_name or orders
        
        filtered = []

        for order in base_list:
            ativo = order.get('Ativo')
            
            if str(ativo) == str(machine_code):
                filtered.append(order)

        return self._format_to_string(filtered)
    
    def _filter_by_name(self, order):

        stopwords = {
            "a", "o", "as", "os", "um", "uma", "uns", "umas",
            "de", "do", "da", "dos", "das",
            "em", "no", "na", "nos", "nas",
            "por", "com", "para", "e", "que", "é", "ao", "à", "às", "aos",
            "saber", "sobre", "tear", "dilo", "nl19", "hechtenberg", "nli", "sixmeter",
            "iso", "clt-1", "clt-2", "0", "1", "2", "3", "4", "5", "6", "7", "9", "01", "02", "03", "04",
            "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15"
        }

        word1 = {word1 for word1 in self.user_message.lower().split() if word1 not in stopwords}
        word_id = {
            word.lstrip('0') for word in order["ID"].split()
            if word.lstrip('0') not in stopwords
        }
        name = {word2 for word2 in order["Nome"].lower().split() if word2 not in stopwords}


        intersection = word1 & word_id
        id = next(iter(intersection), False)

        if(id):
            return id
        
        intersection = word1 & name

        return next(iter(intersection), False)
    
    def _filter_by_id(self, order):
        pass

    def _format_to_string(self, orders):
        if orders == []:
            return "Nenhuma ordem encontrada"
        
        lines = [self._format_item(item) for item in orders]

        result = "\n".join(lines)

        return result

    def _format_item(self, s):
        return f"""
            ### ORDEM DE SERVIÇO
            *** ID: {s['ID']}
            *** Nome: {s['Nome']}
            *** Problema: {s['Problema']}
            *** Categoria: {s['Categoria']}
            *** Setor: {s['Setor']}
            *** Ativo: {s['Ativo']}
            *** Status: {s['Status']}
            *** Criado em: {s['Criado em']}
            *** Trabalho requisitado: {s['Trabalho requisitado']}
            *** Última modificação: {s['Última modificação']}
            *** Data Esperada: {s['Data Esperada']}
        """

if __name__ == "__main__":
    teste = Filter(["vazio", "vazio", "vazio"], 'quero saber sobre a ordem no dude')
    print(teste.filter_order())