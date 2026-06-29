<img align="center" style='position: fixed' alt="FIAP" width=50 src="https://github.com/PedroCozzati/pipeline_fiap_healthcare/blob/master/TrajetoSaude/frontend/public/assets/fiap.png?raw=true"/>



<div align="center">

<img width="100%" src="https://github.com/PedroCozzati/pipeline_fiap_healthcare/blob/master/TrajetoSaude/frontend/public/assets/trajeto-saude-logo-primary-1200px.png?raw=true" alt="Trajeto Saúde" />

# Plataforma de Engenharia de Dados e IA para o cuidado preventivo da diabetes no trajeto urbano de São Paulo

**TCC — <a href="https://www.fiap.com.br/mba/mba-em-engenharia-de-dados">MBA em Engenharia de Dados</a> · FIAP · Discovery (Case <img width=5% align="center" src="https://github.com/PedroCozzati/pipeline_fiap_healthcare/blob/master/TrajetoSaude/frontend/public/assets/Google-Logo-2015.png?raw=true"/>)**

Professor orientador: Tiago Petroni Taveira

| Integrante | RM | GitHub |
|---|---|---|
| Marcela Bento do Vale | 361949 | [marcelabvale](https://github.com/marcelabvale) |
| Pedro Henrique Cozzati Camillo | 361284 | [PedroCozzati](https://github.com/PedroCozzati) |
| Thomaz Colalillo Navajas | 140560 | [NavajasThomaz](https://github.com/NavajasThomaz) |
| Yasmin Martins Vasconcellos | 363354 | [yamars-dev](https://github.com/yamars-dev) |

</div>

##### <div align="center"><a href=https://youtu.be>🖥️Link para Video de pitch.🖥️</a></div>


## Sobre o projeto

O **Trajeto Saúde** é uma plataforma de microserviços que integra dados urbanos, modelos de machine learning e IA generativa (Vertex AI) para apoiar o cuidado preventivo de pacientes com diabetes em São Paulo.

A aplicação é composta por:

| Serviço | Porta | Responsabilidade |
|---|---:|---|
| **frontend** | 4200 | Interface Angular |
| **gateway** | 8000 | API unificada e roteamento |
| **auth** | 8003 | Autenticação JWT e usuários |
| **storage** | 8001 | Cloud Storage e Cloud SQL |
| **prediction** | 8002 | Pipeline de dados e predição de risco |
| **sentinel** | 8004 | Chat Sentinel.AI (Vertex Reasoning Engine) |

### Arquitetura

```mermaid
flowchart TB
    subgraph local["Sua máquina (Docker Compose)"]
        FE[Frontend :4200]
        GW[Gateway :8000]
        AUTH[Auth :8003]
        STOR[Storage :8001]
        PRED[Prediction :8002]
        SENT[Sentinel :8004]
    end

    subgraph gcp["Google Cloud Platform"]
        GCS[(Cloud Storage)]
        SQL[(Cloud SQL PostgreSQL)]
        VERTEX[Vertex AI Reasoning Engine]
    end

    FE --> GW
    GW --> AUTH & STOR & PRED & SENT
    AUTH --> SQL
    STOR --> GCS & SQL
    PRED --> GCS
    SENT --> VERTEX
```

---

## Pré-requisitos

### Obrigatórios (ambos os fluxos)

| Ferramenta | Versão mínima | Verificação |
|---|---|---|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | 24+ | `docker --version` |
| [Docker Compose](https://docs.docker.com/compose/) | v2+ | `docker compose version` |
| Conta [Google Cloud](https://cloud.google.com/) | com billing ativo | — |

### Adicionais para provisionamento com Terraform

| Ferramenta | Versão mínima | Verificação |
|---|---|---|
| [Terraform](https://developer.hashicorp.com/terraform/install) | 1.5+ | `terraform version` |
| [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) | atual | `gcloud version` |

### Serviços GCP utilizados

| Serviço | Obrigatório | Finalidade |
|---|---|---|
| **Cloud SQL** (PostgreSQL) | Sim | Usuários e dados da aplicação |
| **Cloud Storage** | Sim* | Artefatos de modelo e pipeline |
| **IAM / Service Account** | Sim | Autenticação dos microserviços |
| **Vertex AI** (Reasoning Engine) | Não | Chat Sentinel.AI (opcional) |

\* Com `MODEL_SOURCE=local`, o bucket é opcional para rodar predições, mas ainda é usado pelo pipeline de ingestão.

---

## Escolha o fluxo de execução

Existem **duas formas** de executar o projeto. Ambas usam Docker na máquina local; a diferença está em como a infraestrutura GCP é criada.

| | Opção A — Terraform (recomendado) | Opção B — Configuração manual |
|---|---|---|
| **Para quem** | Quem quer reproduzir tudo com um comando | Quem já tem recursos GCP ou prefere o console |
| **Infra GCP** | Criada automaticamente | Criada manualmente no console |
| **Arquivo `.env`** | Gerado por script | Copiado e editado à mão |
| **Tempo estimado** | ~15 min (inclui Cloud SQL) | ~30 min |

---

## Opção A — Terraform + Docker (recomendado)

Provisiona automaticamente: APIs, service account, bucket GCS, Cloud SQL e arquivo `.env`.

### 1. Clone o repositório

```bash
git clone https://github.com/PedroCozzati/pipeline_fiap_healthcare.git
cd pipeline_fiap_healthcare/TrajetoSaude
```

### 2. Autentique no Google Cloud

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project SEU_PROJECT_ID
```

Crie um projeto GCP (se necessário) em [console.cloud.google.com](https://console.cloud.google.com/) e ative o **billing**.

### 3. Provisione a infraestrutura

**Windows (PowerShell):**

```powershell
.\scripts\setup-gcp.ps1 -ProjectId "SEU_PROJECT_ID"
```

**Linux / macOS:**

```bash
chmod +x scripts/*.sh
./scripts/setup-gcp.sh SEU_PROJECT_ID
```

O script executa `terraform init`, `plan` e `apply`, gera `credentials/gcp-sa.json` e cria o `.env` automaticamente.

> **Custo estimado:** a instância Cloud SQL `db-f1-micro` e o bucket GCS têm custo baixo para demonstração. Destrua os recursos após a avaliação com `cd infra && terraform destroy`.

### 4. Suba os microserviços

```bash
docker compose up --build
```

Aguarde todos os healthchecks ficarem verdes (~2–3 min na primeira build).

### 5. Treine o modelo (primeira execução)

O repositório não inclui o arquivo `risk_model.joblib`. Gere-o com dados de demonstração:

**Windows:**

```powershell
.\scripts\train-model.ps1
```

**Linux / macOS:**

```bash
./scripts/train-model.sh
```

Ou via API diretamente:

```bash
curl -X POST http://localhost:8002/ingest/run
```

### 6. Acesse a aplicação

| Recurso | URL |
|---|---|
| Frontend | http://localhost:4200 |
| API Gateway | http://localhost:8000/docs |
| Auth | http://localhost:8003/docs |
| Storage | http://localhost:8001/docs |
| Prediction | http://localhost:8002/docs |
| Sentinel | http://localhost:8004/docs |

### Verificação rápida

```bash
curl http://localhost:8000/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

---

## Opção B — Docker local + GCP manual

Use este fluxo se preferir criar os recursos pelo console ou já possuir um projeto configurado.

### 1. Clone e entre na pasta

```bash
git clone https://github.com/PedroCozzati/pipeline_fiap_healthcare.git
cd pipeline_fiap_healthcare/TrajetoSaude
```

### 2. Crie os recursos no GCP

#### 2.1 Projeto e APIs

No [Console GCP](https://console.cloud.google.com/):

1. Crie ou selecione um projeto
2. Ative as APIs: **Cloud Storage**, **Cloud SQL Admin**, **IAM**, **Vertex AI**

Ou via CLI:

```bash
gcloud services enable storage.googleapis.com sqladmin.googleapis.com iam.googleapis.com aiplatform.googleapis.com
```

#### 2.2 Service Account

1. Acesse **IAM & Admin → Service Accounts → Create**
2. Nome sugerido: `trajeto-app`
3. Conceda os papéis:
   - `Storage Object Admin`
   - `Cloud SQL Client`
   - `Vertex AI User` (opcional, para Sentinel)
4. Crie uma chave JSON e salve em:

```
TrajetoSaude/credentials/gcp-sa.json
```

#### 2.3 Cloud Storage

1. **Cloud Storage → Create bucket**
2. Escolha um nome globalmente único (ex.: `meu-projeto-trajeto-data`)
3. Região: mesma do Cloud SQL (ex.: `us-central1`)

#### 2.4 Cloud SQL (PostgreSQL)

1. **SQL → Create instance → PostgreSQL 15**
2. Tier: `db-f1-micro` (suficiente para demonstração)
3. Crie banco: `trajeto_saude`
4. Crie usuário: `app_user` com senha segura
5. Anote o **Connection name** (formato: `projeto:região:instância`)

### 3. Configure o ambiente

```bash
cp .env.example .env
```

Edite o `.env` com os valores do seu projeto:

```env
GCP_PROJECT_ID=seu-projeto-gcp
GCP_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=credentials/gcp-sa.json
GCP_SA_KEY_FILE=./credentials/gcp-sa.json

GCS_BUCKET_NAME=seu-bucket
CLOUD_SQL_INSTANCE_CONNECTION_NAME=seu-projeto:us-central1:sua-instancia
CLOUD_SQL_DATABASE=trajeto_saude
CLOUD_SQL_USER=app_user
CLOUD_SQL_PASSWORD=sua-senha

MODEL_SOURCE=local
JWT_SECRET_KEY=uma-chave-secreta-forte
```

### 4. Suba os microserviços

```bash
docker compose up --build
```

### 5. Treine o modelo

```bash
curl -X POST http://localhost:8002/ingest/run
```

---

## Vertex AI — Sentinel.AI (opcional)

O chat de orientação ao paciente usa um **Reasoning Engine** no Vertex AI. Sem ele, os demais módulos funcionam normalmente; apenas os endpoints `/sentinel/*` retornarão erro.

Para habilitar:

1. No console GCP, acesse **Vertex AI → Agent Engine / Reasoning Engines**
2. Crie ou importe o agente do projeto
3. Copie a URL de query (formato `https://REGIAO-aiplatform.googleapis.com/v1/projects/.../reasoningEngines/ID:query`)
4. Adicione ao `.env`:

```env
GCP_REASONING_ENGINE_URL=https://us-central1-aiplatform.googleapis.com/v1/projects/SEU_PROJETO/locations/us-central1/reasoningEngines/ID:query
GCP_REASONING_ENGINE_AGENTE_URL=https://...
```

---

## Estrutura do repositório

```
TrajetoSaude/
├── auth/              # Microserviço de autenticação
├── gateway/           # API Gateway
├── storage/           # GCS + Cloud SQL
├── prediction/        # Pipeline ML e predição
├── sentinel_ai/       # Chat IA (Vertex)
├── frontend/          # Angular
├── data/              # Dados do pipeline (amostra incluída)
├── infra/             # Terraform (GCP)
├── scripts/           # Automação (setup, .env, treino)
├── credentials/       # Chave da service account (não versionada)
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `GCP_PROJECT_ID` | ID do projeto GCP |
| `GCP_REGION` | Região dos recursos |
| `GOOGLE_APPLICATION_CREDENTIALS` | Caminho da chave JSON |
| `GCS_BUCKET_NAME` | Bucket para artefatos |
| `CLOUD_SQL_INSTANCE_CONNECTION_NAME` | Connection name do Cloud SQL |
| `CLOUD_SQL_DATABASE` | Nome do banco |
| `CLOUD_SQL_USER` / `CLOUD_SQL_PASSWORD` | Credenciais do banco |
| `MODEL_SOURCE` | `local`, `gcs` ou `vertex` |
| `JWT_SECRET_KEY` | Chave para tokens JWT |
| `GCP_REASONING_ENGINE_URL` | URL do Reasoning Engine (opcional) |

Consulte `.env.example` para a lista completa.

---

## Solução de problemas

### `credentials/gcp-sa.json` não encontrado

Verifique se a chave existe em `TrajetoSaude/credentials/gcp-sa.json` e se `GCP_SA_KEY_FILE=./credentials/gcp-sa.json` no `.env`.

### Auth ou Storage com erro de banco

- Confirme `CLOUD_SQL_INSTANCE_CONNECTION_NAME` no formato `projeto:região:instância`
- Verifique usuário, senha e nome do banco
- A service account precisa do papel **Cloud SQL Client**
- Os containers usam o [Cloud SQL Python Connector](https://cloud.google.com/sql/docs/postgres/connect-connectors) — não é necessário Cloud SQL Proxy

### Prediction sem modelo (`model_loaded: false`)

Execute o treino:

```bash
curl -X POST http://localhost:8002/ingest/run
```

### Porta já em uso

Altere o mapeamento em `docker-compose.yml` ou encerre o processo que ocupa a porta.

### Terraform: bucket name already exists

Defina um nome único em `infra/terraform.tfvars`:

```hcl
gcs_bucket_name = "meu-nome-unico-trajeto"
```

### Destruir recursos GCP (após avaliação)

```bash
cd infra
terraform destroy
```

---

## Notebooks e pipeline de dados

Os notebooks de análise exploratória e modelagem estão na raiz do repositório (`discovery/`, `src/`). O microserviço **prediction** encapsula o pipeline de treino; os dados de amostra estão em `data/raw/` e `data/output/risk_training.csv`.

---

## Licença e uso acadêmico

Projeto desenvolvido como Trabalho de Conclusão de Curso (TCC) do MBA em Engenharia de Dados da FIAP, no contexto da disciplina Discovery com case Google.
