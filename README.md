# 🧠 IsCoolGPT — Assistente Inteligente em Cloud Computing  
Back-end desenvolvido em FastAPI, utilizando arquitetura em nuvem moderna com Docker, AWS ECS Fargate, ECR e CI/CD com GitHub Actions.

---

## 📌 Visão Geral

O **IsCoolGPT** é um assistente inteligente capaz de receber perguntas de estudantes e consultar múltiplas LLMs (Large Language Models), agregando e filtrando as respostas para gerar um retorno final mais preciso e consistente.

Este backend foi desenvolvido como projeto prático da disciplina de **Cloud Computing**, implementando conceitos essenciais como:

- Docker & containerização  
- Arquitetura serverless via AWS Fargate  
- Deploy automatizado com CI/CD  
- APIs escaláveis com FastAPI  
- Segurança via IAM e Secrets  
- Execução stateless  

---

# 🚀 Tecnologias Utilizadas

### **Backend**
- Python 3.12  
- FastAPI  
- Pydantic  
- Uvicorn  

### **Infraestrutura**
- Docker  
- AWS ECR (Elastic Container Registry)  
- AWS ECS Fargate (Serverless containers)  
- AWS IAM  
- AWS VPC + Security Group  
- AWS CloudWatch Logs  

### **Automação**
- GitHub Actions  
- Testes com Pytest  

---

# 🏗️ Arquitetura da Solução

```text
Desenvolvedor → GitHub (push) 
   -> CI (Testes + Build Docker)
   -> Push da imagem no ECR
   -> CD (deploy automático no ECS)
   -> ECS Fargate executa container
   -> API disponível via IP público

📁 Estrutura do Projeto
arduino
Copiar código
iscoolgpt-backend/
 ├── app/
 │   ├── main.py
 │   ├── schemas.py
 │   ├── aggregator.py
 │   ├── llm_base.py
 │   ├── llms/
 │   │    ├── openai_llm.py
 │   │    ├── gemini_llm.py
 │   │    ├── huggingface_llm.py
 │   │    └── fake_llm.py
 │   └── config.py
 ├── tests/
 │   └── test_health.py
 ├── Dockerfile
 ├── requirements.txt
 └── .github/workflows/
      └── ci.yml
⚙️ Execução Local
1. Criar ambiente virtual
bash
Copiar código
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
2. Instalar dependências
bash
Copiar código
pip install -r requirements.txt
3. Rodar localmente
bash
Copiar código
uvicorn app.main:app --reload
4. Acessar a API
Healthcheck:

bash
Copiar código
http://localhost:8000/health
Swagger (documentação automática):

bash
Copiar código
http://localhost:8000/docs
🐳 Executando via Docker (Local)
Build da imagem
bash
Copiar código
docker build -t iscoolgpt-backend .
Executar container
bash
Copiar código
docker run -p 8000:8000 iscoolgpt-backend
☁️ Deploy na AWS
🔹 1. Amazon ECR
Repositório criado:

Copiar código
iscoolgpt-backend
URI:

bash
Copiar código
005716754979.dkr.ecr.us-east-1.amazonaws.com/iscoolgpt-backend
Tag utilizada pelo CI/CD:

nginx
Copiar código
latest
🔹 2. AWS ECS — Cluster & Serviço
Cluster: iscoolgpt-cluster

Service: iscoolgpt-service

Task Definition: iscoolgpt-task (revisão mais recente)

Execution Role: ecsTaskExecutionRole

Container Name: iscoolgpt-backend

Port: 8000

Security Group liberando apenas:

Tipo	Porta	Origem
TCP	8000	0.0.0.0/0

🔄 CI/CD — GitHub Actions
O workflow ci.yml realiza:

✔ Testes automatizados
✔ Build da imagem Docker
✔ Login no ECR
✔ Push da imagem latest
✔ Atualização automática do ECS Service
✔ Deploy imediato da nova Task
Trecho principal do arquivo CI/CD:

yaml
Copiar código
# (código completo do seu ci.yml aqui)
Secrets configurados no GitHub Actions:

AWS_ACCESS_KEY_ID

AWS_SECRET_ACCESS_KEY

AWS_REGION

ECR_REGISTRY

ECS_REPOSITORY

ECS_CLUSTER

ECS_SERVICE

🧪 Testando a API na AWS
Obtenha o IP público da sua Task:

ECS → Cluster → Service → Tasks → Task → Network → Public IP

Healthcheck:

arduino
Copiar código
http://SEU-IP:8000/health
Swagger:

arduino
Copiar código
http://SEU-IP:8000/docs
📈 Testes
Exemplo simples incluído:

python
Copiar código
def test_health():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
Executar testes localmente:

bash
Copiar código
pytest
🔐 Segurança
Deploy em Fargate (sem servidores expostos)

Security Group mínimo (porta 8000)

Keys protegidas via GitHub Secrets

Task Execution Role com permissões mínimas

Sem credenciais no código

🌱 Possíveis Evoluções

HTTPS com Load Balancer + ACM

Autoscaling baseado em CPU/Memória

CloudFront + domínio customizado

Integração com mais LLMs

Sistema de cache de respostas

Persistência no DynamoDB

Observabilidade com X-Ray

👤 Autor
Vinicius
Projeto desenvolvido para a disciplina de Cloud Computing
2025