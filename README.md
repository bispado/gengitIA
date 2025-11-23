# GenFit

Sistema completo de recrutamento inteligente com integração de IA generativa (OpenAI GPT) para análise, rankeamento e gestão de candidatos.

## 🎥 Demonstração

Assista ao vídeo de demonstração do sistema: [GenFit - Demonstração](https://youtu.be/razi04CvtIk)

## 🎯 Funcionalidades

- ✅ **Rankeamento de Candidatos com IA**: Analisa e classifica candidatos para vagas usando GPT-4
- ✅ **Resgate de Banco de Talentos com IA**: Busca inteligente no banco de talentos usando processamento de linguagem natural
- ✅ **Análise Detalhada**: Análise completa de compatibilidade com recomendações e perguntas sugeridas
- ✅ **Cadastro Completo**: Usuários (candidatos e funcionários) e vagas
- ✅ **Gerenciamento de Skills**: Catálogo, adição a candidatos e vagas
- ✅ **Análise de IA Generativa**: Análise detalhada de compatibilidade cultural e profissional
- ✅ **Red Flags**: Identificação automática de pontos de atenção nos candidatos
- ✅ **Cálculo de Compatibilidade**: Usando funções do banco Oracle
- ✅ **Comentários e Agendamento**: Sistema de comentários e agendamento de reuniões

## 📋 Pré-requisitos

- Python 3.9 ou superior
- Oracle Database 19c (acesso ao banco FIAP)
- Conta OpenAI com API Key
- Conta de email SMTP (Gmail recomendado)

## 🚀 Como Rodar Localmente

### 1. Clone o Repositório

```bash
git clone <url-do-repositorio>
cd iot
```

### 2. Crie um Ambiente Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as Variáveis de Ambiente

Copie o arquivo `env.example` para `.env`:

```bash
# Windows
copy env.example .env

# Linux/Mac
cp env.example .env
```

Edite o arquivo `.env` e configure suas credenciais:

```env
# Oracle Database
ORACLE_USER=rm558515
ORACLE_PASSWORD=sua_senha
ORACLE_HOST=oracle.fiap.com.br
ORACLE_PORT=1521
ORACLE_SID=ORCL

# OpenAI API (OBRIGATÓRIO)
OPENAI_API_KEY=sk-sua-chave-aqui

# Email SMTP (para envio de convites)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_app
EMAIL_FROM=noreply@futurwork.com

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=True
```

**⚠️ IMPORTANTE**:

- Para Gmail, você precisa criar uma [Senha de App](https://support.google.com/accounts/answer/185833)
- Obtenha sua API Key no [OpenAI Platform](https://platform.openai.com/api-keys)

### 5. Execute a API

```bash
python main.py
```

Ou usando uvicorn diretamente:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em: `http://localhost:8000`

## 📚 Documentação da API

Após iniciar a API, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testando a API

### Health Check

```bash
curl http://localhost:8000/health
```

### Exemplo: Criar Candidato

```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva",
    "email": "joao@email.com",
    "role": "candidate",
    "cpf": "123.456.789-00"
  }'
```

### Exemplo: Criar Vaga

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Desenvolvedor Python",
    "descricao": "Vaga para desenvolvedor Python",
    "salario": 10000.00,
    "nivel": "Pleno"
  }'
```

### Exemplo: Ver Perfil do Candidato

```bash
curl http://localhost:8000/api/candidates/1/profile
```

### Exemplo: Listar Vagas

```bash
curl http://localhost:8000/api/jobs
```

### Exemplo: Rankear Candidatos

O endpoint de ranking analisa todos os candidatos disponíveis e retorna um ranking ordenado por compatibilidade, incluindo análise de IA generativa:

```bash
curl -X POST http://localhost:8000/api/candidates/ranking \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 18,
    "limit": 5,
    "min_compatibility": 50.0
  }'
```

**Resposta esperada:**
```json
[
  {
    "candidate_id": 5,
    "candidate_name": "Carlos Mendes",
    "candidate_email": "carlos.mendes@email.com",
    "compatibility_score": 70.0,
    "cultural_fit_score": 50.0,
    "professional_fit_score": 80.0,
    "ai_analysis": "Análise detalhada gerada pela IA...",
    "red_flags": ["Falta de experiência mencionada"],
    "recommendation": "EM_ANALISE"
  }
]
```

**Parâmetros:**
- `job_id`: ID da vaga para rankear
- `limit`: Número máximo de candidatos a retornar
- `min_compatibility`: Score mínimo de compatibilidade (0-100)

## 📁 Estrutura do Projeto

```
iot/
├── main.py                 # API FastAPI principal
├── config.py               # Configurações da aplicação
├── database.py             # Conexão Oracle
├── models.py               # Modelos Pydantic
├── requirements.txt        # Dependências Python
├── env.example             # Exemplo de variáveis de ambiente
├── README.md               # Este arquivo
│
└── services/
    ├── __init__.py
    ├── ai_service.py       # Serviço de IA (OpenAI)
    ├── database_service.py # Serviço de banco de dados
    └── email_service.py    # Serviço de email
```

## 🔧 Configuração do Banco de Dados

Certifique-se de que o banco Oracle está configurado e acessível. As configurações de conexão estão no arquivo `.env`.

### Dados de Exemplo

O projeto inclui scripts para popular o banco com dados de exemplo:

```bash
# Popula candidatos e vagas de exemplo
python populate_examples.py

# Adiciona dados adicionais (se necessário)
python add_examples_data.py
```

**Nota**: Certifique-se de ter skills cadastradas no banco e associadas aos candidatos e vagas para que o ranking funcione corretamente. O ranking utiliza as skills dos candidatos e as skills requeridas pela vaga para calcular a compatibilidade.

## 💡 Funcionalidades do Ranking

O sistema de ranking utiliza IA generativa (GPT-4) para:

- **Análise de Compatibilidade**: Calcula score de 0-100 baseado em skills, experiência e fit
- **Análise Cultural**: Avalia o fit cultural do candidato com a empresa
- **Análise Profissional**: Avalia as habilidades técnicas e experiência profissional
- **Red Flags**: Identifica automaticamente pontos de atenção (falta de skills, experiência, etc.)
- **Recomendações**: Sugere próximos passos (EM_ANALISE, RECOMENDADO, etc.)

**Importante**: Para que o ranking funcione corretamente, é necessário:
1. Candidatos cadastrados com skills associadas
2. Vagas cadastradas com skills requeridas
3. API Key do OpenAI configurada no `.env`

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'oracledb'"

```bash
pip install oracledb
```

### Erro: "ORA-12154: TNS:could not resolve the connect identifier"

Verifique as configurações do Oracle no arquivo `.env` e certifique-se de que o banco está acessível.

### Erro: "OpenAI API key not found"

Configure `OPENAI_API_KEY` no arquivo `.env`.

### Erro ao enviar email

Para Gmail:

1. Ative a verificação em 2 etapas
2. Crie uma [Senha de App](https://support.google.com/accounts/answer/185833)
3. Use a senha de app no `SMTP_PASSWORD`

## 📝 Endpoints Principais

- `GET /` - Endpoint raiz
- `GET /health` - Health check
- `GET /docs` - Documentação Swagger
- `POST /api/users` - Criar usuário
- `GET /api/users` - Listar usuários
- `POST /api/jobs` - Criar vaga
- `GET /api/jobs` - Listar vagas
- `POST /api/candidates/ranking` - Rankear candidatos com IA
- `POST /api/talent-pool/search` - Buscar no banco de talentos com IA
- `POST /api/ai/analyze` - Análise detalhada de IA

Para ver todos os endpoints, acesse: http://localhost:8000/docs

## 🔗 Links Úteis

- [OpenAI Platform](https://platform.openai.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Oracle Database](https://www.oracle.com/database/)

## 👥 Autores

- **Vinicius Murtinho Vicente** - RM551151
- **Lucas Barreto Consentino** - RM557107
- **Gustavo Bispo Cordeiro** - RM558515

## 📝 Licença

Projeto educacional desenvolvido para FIAP.

---

**Desenvolvido com ❤️ para o futuro do trabalho**
