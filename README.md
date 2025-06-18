```markdown
# Chatbot-Project-FullStack

Este repositório contém um projeto completo de chatbot full-stack, dividido em três componentes principais: a API (backend), o Modelo (inteligência do chatbot) e a Interface Web (frontend).

## Visão Geral

Este chatbot tem como objetivo **fornecer um sistema de consulta interna para a Andritz, permitindo que os usuários realizem consultas tanto na internet quanto em bancos de dados internos.**

## Estrutura do Projeto

O repositório é organizado nas seguintes pastas:

* **`API/`**: Contém a lógica de backend e os endpoints da API para interação com o modelo do chatbot e o banco de dados. Desenvolvida em Node.js (ATUALMENTE USANDO C# COM RABBITMQ).
* **`Modelo/`**: Abriga a inteligência do chatbot, incluindo o processamento de linguagem natural (PLN), lógica de conversação e integração com dados. Desenvolvida em Python.
* **`WebInterface/andritz_ai/`**: O frontend do chatbot, proporcionando uma interface de usuário interativa para a comunicação com o chatbot. Desenvolvida utilizando Next.js.

## Tecnologias Utilizadas

### API (Node.js)

* **Linguagem:** JavaScript (Node.js)
* **Framework Web:** Express
* **Outras bibliotecas notáveis:**
    * `WebSockets`: Polling.
    * `cors`: Para lidar com requisições de diferentes origens.
    * `body-parser`: Para analisar o corpo das requisições HTTP.
    * `debug`: Utilitário de depuração.
    * `http-errors`: Cria objetos de erro HTTP.
    * `cookie`, `cookie-signature`: Para manipulação de cookies.
    * `qs`: Para parsear strings de query.
    * `send`, `serve-static`: Para servir arquivos estáticos.
    * `accepts`, `array-flatten`, `bytes`, `content-disposition`, `content-type`, `depd`, `destroy`, `encodeurl`, `etag`, `finalhandler`, `forwarded`, `fresh`, `media-typer`, `merge-descriptors`, `methods`, `mime`, `mime-db`, `mime-types`, `ms`, `negotiator`, `on-finished`, `parseurl`, `path-to-regexp`, `proxy-addr`, `range-parser`, `raw-body`, `safe-buffer`, `safer-buffer`, `toidentifier`, `type-is`, `unpipe`, `utils-merge`, `vary`: Diversas bibliotecas de utilidade para Express e manipulação de HTTP.
    * `iconv-lite`: Para conversão de codificação de caracteres.
    * `call-bind-apply-helpers`, `call-bound`, `dunder-proto`, `es-define-property`, `es-errors`, `es-object-atoms`, `escape-html`, `function-bind`, `get-intrinsic`, `get-proto`, `gopd`, `has-symbols`, `hasown`, `inherits`, `ipaddr.js`, `math-intrinsics`, `object-inspect`, `setprototypeof`, `side-channel`, `side-channel-list`, `side-channel-map`, `side-channel-weakmap`, `statuses`: Bibliotecas auxiliares e de baixo nível.

### Modelo (Python)

* **Linguagem:** Python
* **Bibliotecas notáveis (deduzidas pelos nomes dos arquivos):**
    * `src/customers/customer.py`: Lógica relacionada a clientes.
    * `src/db_logs/receive.py`, `src/db_logs/toggleReceive.py`: Possivelmente para gerenciamento de logs de banco de dados.
    * `src/dude/`: Parece conter lógica para alguma entidade "dude", com `controller.py`, `dude.py`, `filter.py`, `formated_machines.py`.
    * `src/helpers/context.py`, `src/helpers/users.py`: Utilitários e gerenciamento de contexto/usuários.
    * `src/machine_data/`: Módulos para dados de máquinas (`machineName.py`, `machines_ids.py`, `node_id_map.py`, `status.py`).
    * `src/machines/machines.py`: Lógica principal para máquinas.
    * `src/product_data/`: Módulos para dados de produtos (`node_id_map.py`, `productName.py`, `products_ids.py`, `status.py`).
    * `src/prompts/`: Contém os prompts e a lógica para o RAG (Retrieval-Augmented Generation) (`AdvancedPrompts.py`, `commands.py`, `index_data_for_rag.py`, `prompts.py`).
    * `src/user_conversation/conversation.py`: Gerenciamento da conversa do usuário.
    * `manual_estruturado.json`: Dados estruturados, provavelmente usados pelo modelo.

### Interface Web (Next.js)

* **Framework:** Next.js
* **Linguagem:** JavaScript/JSX
* **Bibliotecas notáveis (deduzidas pelos nomes dos arquivos):**
    * `next-auth`: Para autenticação de usuários.
    * `react`, `react-dom`: Bibliotecas fundamentais do React.
    * `tailwind-merge`, `tailwindcss-animate`: Para estilização com Tailwind CSS.
    * `class-variance-authority`, `clsx`: Utilitários para classes CSS.
    * `framer-motion`: Para animações.
    * `lucide-react`: Para ícones.
    * `bcryptjs`: Para hash de senhas.
    * `components/ui/`: Componentes de UI reutilizáveis (botões, cards, inputs).
    * `src/app/api/auth/[...nextauth]/route.js`: Rotas de API para autenticação.
    * `src/app/api/presence/logout/route.js`, `src/app/api/presence/route.js`: Rotas de API para gerenciamento de presença.
    * `src/app/chat/page.js`: Página principal do chat.
    * `src/app/login/page.jsx`, `src/app/page.jsx`: Páginas de login e inicial.
    * `src/app/providers.jsx`: Provedores de contexto/sessão.
    * `src/lib/auth.js`, `src/lib/db.js`, `src/lib/utils.js`: Utilitários e configurações.

## Requisitos de Sistema

* Node.js (versão **deduzida do `package.json` da API: ^4.16.2 ou superior**)
* Python (versão **[PRECISA PREENCHER: A versão exata do Python, por exemplo, 3.9+]**)
* npm ou yarn (versão **deduzida do `package.json` da API e WebInterface: `>=8.0.0` para npm, ou a versão correspondente para yarn**)
* **Banco de Dados:** SQL Server (e futura integração com DynamoDB)

```

#### `Modelo/.env`

```env
# Adicione variáveis de ambiente para o modelo Python, como chaves de API para serviços de PLN, etc.
# Ex: OPENAI_API_KEY=your_openai_api_key
# Ex: EMBEDDING_MODEL_PATH=path/to/your/embedding/model
# Ex: RAG_DATA_PATH=path/to/your/rag/data
```

#### `WebInterface/andritz_ai/.env.local`

```env
NEXTAUTH_URL=http://localhost:3000 # Ou a URL da sua aplicação Next.js
NEXTAUTH_SECRET=your_long_random_secret_string # **ESSENCIAL: Gere uma string secreta aleatória e longa.**
MONGODB_URI=your_mongodb_connection_string # String de conexão do MongoDB, usada para autenticação.
# Adicione quaisquer outras variáveis de ambiente que o frontend possa precisar.
# Ex: NEXT_PUBLIC_API_URL=http://localhost:5000/api
```

## Instalação

Siga as instruções abaixo para configurar e rodar cada parte do projeto.

### 1. Modelo (Python)

```bash
# Navegue até a pasta do modelo
cd Modelo/

# Crie e ative um ambiente virtual (recomendado)
python -m venv venv
# No Linux/macOS
source venv/bin/activate
# No Windows
.\venv\Scripts\activate

# Instale as dependências (certifique-se de ter um requirements.txt atualizado)
# Se você não tiver um requirements.txt, crie um com as bibliotecas Python que seu modelo utiliza.
# Exemplo de criação do requirements.txt (se o projeto não tiver um):
# pip freeze > requirements.txt
pip install -r requirements.txt

# Se o modelo precisar de inicialização de dados para o RAG, execute o script:
python src/prompts/index_data_for_rag.py
```

### 2. API (Node.js)

```bash
# Navegue até a pasta da API
cd API/

# Instale as dependências
npm install # ou yarn install
```

### 3. Interface Web (Next.js)

```bash
# Navegue até a pasta da interface web
cd WebInterface/andritz_ai/

# Instale as dependências
npm install # ou yarn install
```

## Como Executar

Certifique-se de que cada componente esteja rodando na ordem correta para que o sistema funcione adequadamente.

### 1. Iniciar o Modelo (Python)

```bash
# Navegue até a pasta do modelo
cd Modelo/

# Ative o ambiente virtual (se ainda não estiver ativo)
source venv/bin/activate # No Linux/macOS
.\venv\Scripts\activate # No Windows

# Inicie o script principal do modelo
python src/main.py
```

### 2. Iniciar a API (Node.js)

```bash
# Navegue até a pasta da API
cd API/

# Inicie o servidor da API
npm start # ou node server.js
```

### 3. Iniciar a Interface Web (Next.js)

```bash
# Navegue até a pasta da interface web
cd WebInterface/andritz_ai/

# Inicie o servidor de desenvolvimento do Next.js
npm run dev
```

A interface web estará disponível em `http://localhost:3000` (ou a porta configurada no `NEXTAUTH_URL`).

## Uso

Após iniciar todos os serviços (Modelo, API e Interface Web), acesse a interface web em seu navegador. Você poderá **fazer login no sistema e utilizar o chatbot para realizar suas consultas internas. O chatbot processará suas requisições, buscando informações tanto na internet quanto nos bancos de dados internos (SQL Server e, futuramente, DynamoDB) para fornecer respostas relevantes.**

## Contribuição

Sinta-se à vontade para contribuir com este projeto! Para isso:
1.  Faça um fork do repositório.
2.  Crie uma nova branch para sua feature (`git checkout -b feature/sua-feature`).
3.  Faça suas alterações e commit-as (`git commit -m 'feat: Adiciona nova funcionalidade'`).
4.  Envie para o branch remoto (`git push origin feature/sua-feature`).
5.  Abra um Pull Request descrevendo suas mudanças.

```
