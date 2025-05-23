from dude.dude import DudeSolutions

class Filter:

    def __init__(self, bot_message, user_message):
        self.bot_message = bot_message
        self.user_message = user_message

    def filter_order(self):
        filter = DudeSolutions(self.bot_message[0], self.bot_message[1])
        filtered = filter.getOrderBy()

        filtered_by_machine = self._filter_by_machine(filtered)

        return filtered_by_machine


    def _filter_by_machine(self, orders):
        machine_code = self.bot_message[2]
        print(f"Maquina: {self.bot_message[2]}")

        by_name = [order for order in orders if self._filter_by_name(order)]
        print(f"by_name: {by_name}")

        if machine_code == 'vazio':
            result = by_name if by_name else orders
            return self._format_to_string(result)

        base_list = by_name or orders
        
        filtered = [order for order in base_list if str(order.get('Ativo')) == str(machine_code)]
        print(f"filtered: {filtered}")
        return self._format_to_string(filtered)
    
    def _filter_by_name(self, order):

        stopwords = {
            "a", "o", "as", "os", "um", "uma", "uns", "umas",
            "de", "do", "da", "dos", "das",
            "em", "no", "na", "nos", "nas",
            "por", "com", "para", "e", "que", "é", "ao", "à", "às", "aos",
            "saber", "sobre", "tear", "dilo", "nl19", "hechtenberg", "nli", "sixmeter",
            "iso", "0", "1", "2", "3", "4", "5", "6", "7", "9"
        }

        word1 = {word1 for word1 in self.user_message.lower().split() if word1 not in stopwords}
        word2 = {word2 for word2 in order["Nome"].lower().split() if word2 not in stopwords}

        intersection = word1 & word2

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
    teste = Filter(["vazio", "Completed", "Tear 09 - Jurgens 11.7"], "pancada")
    print(teste.filter_order())