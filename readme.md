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
<div align="center"><a href=https://youtu.be>🖥️Link para Video de pitch.🖥️</a>
</div>


**Evidência do MVP** — acesse em: <a href="https://trajeto-frontend-bzxse6rn6q-uc.a.run.app/">trajeto-frontend-bzxse6rn6q-uc.a.run.app</a>

<div align="center">

<video src="traj-saude-speedup.mp4" controls width="100%" title="Trajeto Saúde — Demo"></video>

</div>


## Sobre o projeto

O **Trajeto Saúde** é uma plataforma de microserviços que integra dados urbanos, modelos de machine learning e IA generativa (**Vitta.AI**, powered by Vertex AI Agent Engine + Gemini 3.5 Flash) para apoiar o cuidado preventivo de pacientes com diabetes em São Paulo.

A aplicação é composta por:

| Serviço | Porta | Responsabilidade |
|---|---:|---|
| **frontend** | 4200 | Interface Angular |
| **gateway** | 8000 | API unificada e roteamento |
| **auth** | 8003 | Autenticação JWT e usuários |
| **storage** | 8001 | Cloud Storage e Cloud SQL |
| **prediction** | 8002 | Pipeline de dados e predição de risco |
| **sentinel** | 8004 | Chat Vitta.AI (Vertex AI Agent Engine) |

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
        subgraph vertex["Vertex AI Agent Engine"]
            A1[Vitta.AI Paciente]
            A2[Vitta.AI Agente de Saúde]
            A3[Vitta.AI UBS por 3km]
        end
    end

    FE --> GW
    GW --> AUTH & STOR & PRED & SENT
    AUTH --> SQL
    STOR --> GCS & SQL
    PRED --> GCS
    SENT --> vertex
```

---

## Pré-requisitos

### Obrigatórios (todos os fluxos)

| Ferramenta | Versão mínima | Verificação |
|---|---|---|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | 24+ | `docker --version` |
| [Terraform](https://developer.hashicorp.com/terraform/install) | 1.5+ | `terraform version` |
| [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) | atual | `gcloud version` |
| Conta [Google Cloud](https://cloud.google.com/) | com billing ativo | — |

Na **Opção A (Cloud Run)**, o Docker é usado apenas para *buildar* as imagens antes do push ao Artifact Registry — a aplicação em si roda inteiramente no GCP, sem containers locais em execução. Nas opções B e C, o Docker também executa a stack localmente (`docker compose up`).

### Adicionais apenas para as Opções B/C (Docker Compose local)

| Ferramenta | Versão mínima | Verificação |
|---|---|---|
| [Docker Compose](https://docs.docker.com/compose/) | v2+ | `docker compose version` |

### Serviços GCP utilizados

| Serviço | Obrigatório | Finalidade |
|---|---|---|
| **Cloud SQL** (PostgreSQL 15) | Sim | Usuários e dados da aplicação |
| **Cloud Storage** | Sim* | Artefatos de modelo e pipeline |
| **IAM / Service Account** | Sim | Autenticação dos microserviços |
| **Artifact Registry** | Apenas na Opção A | Armazena as imagens Docker publicadas |
| **Cloud Run** | Apenas na Opção A | Execução dos microserviços na nuvem |
| **Vertex AI Agent Engine** | Apenas na Opção A | Três agentes Vitta.AI (google-adk + Gemini 3.5 Flash) |

\* Com `MODEL_SOURCE=local` (Opções B/C), o bucket é opcional para rodar predições, mas ainda é usado pelo pipeline de ingestão. Na Opção A, o `prediction` sempre usa `MODEL_SOURCE=gcs`.

---

## Escolha o fluxo de execução

Existem **três formas** de executar o projeto:

| | Opção A — Full GCP / Cloud Run (principal) | Opção B — Terraform + Docker local | Opção C — Configuração manual |
|---|---|---|---|
| **Onde os containers rodam** | Cloud Run (GCP) | Docker na sua máquina | Docker na sua máquina |
| **Para quem** | Quer a aplicação publicada e acessível por URL, sem depender da máquina local | Quer reproduzir tudo localmente com um comando | Já tem recursos GCP ou prefere o console |
| **Infra GCP** | Criada automaticamente (+ imagens publicadas no Artifact Registry) | Criada automaticamente | Criada manualmente no console |
| **Agentes Vitta.AI** | Criados e gerenciados pelo Terraform via Vertex AI Agent Engine | Não disponíveis (opcional, local) | Configuração manual no console |
| **Configuração da app** | Variáveis injetadas direto nos serviços Cloud Run pelo Terraform | Arquivo `.env` gerado por script | `.env` copiado e editado à mão |
| **Tempo estimado** | ~25–30 min (inclui build, push e criação dos agentes IA) | ~15 min (inclui Cloud SQL) | ~30 min |

---

## Opção A — Full GCP / Cloud Run (principal)

Toda a stack roda no GCP: Cloud SQL, Cloud Storage, os 6 microserviços em **Cloud Run** e os três agentes **Vitta.AI** no **Vertex AI Agent Engine** — tudo provisionado pelo Terraform.

```mermaid
flowchart TB
    subgraph cloudrun["Cloud Run"]
        FE[frontend]
        GW[gateway]
        AUTH[auth]
        STOR[storage]
        PRED[prediction]
        SENT[sentinel]
    end

    subgraph gcp["Google Cloud Platform"]
        AR[(Artifact Registry)]
        GCS[(Cloud Storage)]
        SQL[(Cloud SQL PostgreSQL)]
        subgraph vertex["Vertex AI Agent Engine"]
            A1[Vitta.AI Paciente]
            A2[Vitta.AI Agente de Saúde]
            A3[Vitta.AI UBS por 3km]
        end
    end

    Usuario((Usuário)) --> FE
    FE --> GW
    GW --> AUTH & STOR & PRED & SENT
    AUTH --> SQL
    STOR --> GCS & SQL
    PRED --> GCS & STOR
    SENT --> vertex
    AR -.imagens.-> FE & GW & AUTH & STOR & PRED & SENT
```

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

### 3. Implante a infraestrutura e a aplicação

**Windows (PowerShell):**

```powershell
.\scripts\deploy-cloudrun.ps1 -ProjectId "SEU_PROJECT_ID"
```

**Linux / macOS:**

```bash
chmod +x scripts/*.sh scripts/package-agents.sh
./scripts/deploy-cloudrun.sh SEU_PROJECT_ID
```

O script executa, em sequência:

1. `terraform apply` da infraestrutura base (APIs, service account, Cloud SQL, bucket GCS, Artifact Registry e **3 agentes Vitta.AI** no Vertex AI Agent Engine);
2. build e push das 6 imagens Docker (`auth`, `storage`, `prediction`, `sentinel`, `gateway`, `frontend`) para o Artifact Registry;
3. `terraform apply` com `deploy_cloud_run=true`, criando os serviços Cloud Run com as URLs dos agentes Vitta.AI já injetadas como env vars;
4. `POST /api/seed` para popular o banco com dados de demonstração.

Ao final, o script imprime a URL pública de cada serviço.

> **Custo estimado:** Cloud SQL `db-f1-micro`, bucket GCS, serviços Cloud Run (escalam a zero) e Vertex AI Agent Engine (cobrança por uso) têm custo baixo para demonstração. Destrua os recursos após a avaliação com `cd infra && terraform destroy`.

### 4. Treine o modelo

O serviço `prediction` não inclui um `risk_model.joblib` pronto — gere-o chamando o endpoint de ingestão na URL pública do Cloud Run:

**Windows:**

```powershell
$env:PREDICTION_URL = (terraform -chdir=infra output -raw cloud_run_prediction_url)
.\scripts\train-model.ps1
```

**Linux / macOS:**

```bash
export PREDICTION_URL=$(terraform -chdir=infra output -raw cloud_run_prediction_url)
./scripts/train-model.sh
```

### 5. Acesse a aplicação

```bash
terraform -chdir=infra output cloud_run_frontend_url
terraform -chdir=infra output cloud_run_gateway_url
```

| Recurso | Origem da URL |
|---|---|
| Frontend | `terraform output cloud_run_frontend_url` |
| API Gateway (`/docs` para Swagger) | `terraform output cloud_run_gateway_url` |
| Auth / Storage / Prediction / Sentinel | `terraform output cloud_run_<serviço>_url` |
| URLs dos agentes Vitta.AI | `terraform output agent_engine_query_urls` |

### Atualizando a aplicação

Após alterar código de algum microserviço:

```bash
./scripts/build-push.sh
cd infra && terraform apply -var="deploy_cloud_run=true"
```

### Destruir recursos GCP (após avaliação)

```bash
cd infra
terraform destroy
```

---

## Vitta.AI — Agentes no Vertex AI Agent Engine

O Vitta.AI é composto por três agentes ADK (google-adk + Gemini 3.5 Flash) criados e gerenciados pelo Terraform na Opção A. **Não é necessária nenhuma configuração manual** — as URLs são auto-geradas e injetadas no serviço `sentinel` via Cloud Run env vars.

| Agente | Função |
|---|---|
| **Vitta.AI Paciente** | Chatbot de orientação ao paciente sobre rotas e hubs de saúde |
| **Vitta.AI Agente de Saúde** | Indica 3 UBS próximas da rota de trabalho do paciente |
| **Vitta.AI UBS por 3km** | Calcula quantas UBS existem num raio de 3km da residência |

### Atualizando o código de um agente

1. Edite `infra/agents/<nome>/agent.py`
2. Reempacote:

```bash
./infra/scripts/package-agents.sh
```

3. Aplique no GCP:

```bash
cd infra
# Se o agente tem sessões ativas, delete-o manualmente primeiro:
# gcloud ... (veja seção Solução de Problemas)
terraform apply -var="deploy_cloud_run=true"
```

### Para uso local (Opções B/C)

Nas opções com Docker Compose, os endpoints `/sentinel/*` funcionam mas chamam os agentes diretamente via URLs configuradas em `.env`. Os agentes Vitta.AI já existentes no projeto GCP podem ser reutilizados — copie as URLs do output do Terraform:

```bash
terraform -chdir=infra output agent_engine_query_urls
```

E adicione ao `.env`:

```env
GCP_REASONING_ENGINE_URL=<URL do agente paciente>
GCP_REASONING_ENGINE_AGENTE_URL=<URL do agente de saúde>
GCP_REASONING_ENGINE_UBS_PER_3KM_URL=<URL do agente UBS por 3km>
```

---

## Opção B — Terraform + Docker (local)

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

```powershell
.\scripts\train-model.ps1
```

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

## Opção C — Docker local + GCP manual

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
   - `Storage Legacy Bucket Reader` (em nível de bucket, necessário para `bucket.exists()`)
   - `Cloud SQL Client`
   - `Vertex AI User`
4. Crie uma chave JSON e salve em `TrajetoSaude/credentials/gcp-sa.json`

#### 2.3 Cloud Storage

1. **Cloud Storage → Create bucket** (nome globalmente único, ex.: `meu-projeto-trajeto-data`)
2. Região: mesma do Cloud SQL (ex.: `us-central1`)

#### 2.4 Cloud SQL (PostgreSQL)

1. **SQL → Create instance → PostgreSQL 15**, tier `db-f1-micro`
2. Crie banco `trajeto_saude`, usuário `app_user`
3. Anote o **Connection name** (formato: `projeto:região:instância`)

### 3. Configure o ambiente

```bash
cp .env.example .env
```

Edite o `.env`:

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

## Estrutura do repositório

```
TrajetoSaude/
├── auth/              # Microserviço de autenticação
├── gateway/           # API Gateway
├── storage/           # GCS + Cloud SQL
├── prediction/        # Pipeline ML e predição (+ Dockerfile.cloudrun)
├── sentinel_ai/       # Microsserviço Vitta.AI (chama Vertex AI Agent Engine)
├── frontend/          # Angular (+ Dockerfile.cloudrun, nginx.conf.template)
├── data/              # Dados do pipeline (amostra incluída)
├── infra/             # Terraform — toda a infra GCP
│   ├── agents/        # Código-fonte dos agentes ADK
│   │   ├── sentinela_ai/
│   │   │   ├── agent.py          # Definição do agente (LlmAgent + AdkApp)
│   │   │   ├── requirements.txt
│   │   │   └── source.tar.gz.b64 # Artefato gerado por package-agents.sh
│   │   ├── sentinela_ai_agentedesaude/
│   │   └── sentinel_ai_ubs_per_3km/
│   ├── scripts/
│   │   └── package-agents.sh    # Reempacota agentes após editar agent.py
│   ├── agent_engine.tf  # google_vertex_ai_reasoning_engine (3 agentes)
│   ├── cloudrun.tf
│   ├── cloudsql.tf
│   ├── iam.tf
│   ├── main.tf
│   ├── outputs.tf
│   ├── storage.tf
│   ├── variables.tf
│   └── versions.tf      # google provider ~> 7.0
├── scripts/             # Automação (deploy-cloudrun, build-push, seed, treino)
├── credentials/         # Chave da service account (não versionada; fluxo local)
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
| `GCP_REASONING_ENGINE_URL` | URL do agente Vitta.AI Paciente (auto-injetado na Opção A) |
| `GCP_REASONING_ENGINE_AGENTE_URL` | URL do agente Vitta.AI Agente de Saúde (auto-injetado na Opção A) |
| `GCP_REASONING_ENGINE_UBS_PER_3KM_URL` | URL do agente Vitta.AI UBS por 3km (auto-injetado na Opção A) |

Consulte `.env.example` para a lista completa.

---

## Solução de problemas

### `credentials/gcp-sa.json` não encontrado

Verifique se a chave existe em `TrajetoSaude/credentials/gcp-sa.json` e se `GCP_SA_KEY_FILE=./credentials/gcp-sa.json` no `.env`.

### Auth ou Storage com erro de banco

- Confirme `CLOUD_SQL_INSTANCE_CONNECTION_NAME` no formato `projeto:região:instância`
- Verifique usuário, senha e nome do banco
- A service account precisa dos papéis **Cloud SQL Client** e **Storage Object Admin**
- Os containers usam o [Cloud SQL Python Connector](https://cloud.google.com/sql/docs/postgres/connect-connectors) — não é necessário Cloud SQL Proxy

### Storage com erro 403 no GCS (`bucket.exists()`)

A service account precisa de **Storage Legacy Bucket Reader** em nível de bucket (além do Storage Object Admin no projeto). Na Opção A, o Terraform já provisiona isso automaticamente via `google_storage_bucket_iam_member`.

### Prediction sem modelo (`model_loaded: false`)

```bash
curl -X POST http://localhost:8002/ingest/run
```

Os dados brutos precisam estar em `data/raw/` (PNS 2019, OD 2017, GTFS, GIS).

### Terraform: bucket name already exists

```hcl
# infra/terraform.tfvars
gcs_bucket_name = "meu-nome-unico-trajeto"
```

### Cloud Run (Opção A): `terraform apply` falha com imagem não encontrada

O `terraform apply -var="deploy_cloud_run=true"` espera imagens no Artifact Registry. Rode `./scripts/build-push.ps1` (ou `.sh`) antes — o `deploy-cloudrun` já faz isso na ordem correta.

### Cloud Run (Opção A): frontend não consegue falar com o gateway

O proxy `/api/*` do Nginx usa a env var `GATEWAY_URL`, injetada pelo Terraform. Após recriar o serviço gateway, reaplique:

```bash
cd infra && terraform apply -var="deploy_cloud_run=true"
```

### Cloud Run (Opção A): `/ingest/run` expira (timeout)

O serviço `prediction` tem timeout de 600s no Cloud Run. Verifique os logs:

```bash
gcloud run services logs read trajeto-prediction --region us-central1
```

### Agente Vitta.AI: `terraform apply` falha ao atualizar com "failed to be updated"

O Vertex AI Agent Engine não permite update in-place quando existem sessões ativas. Solução:

```bash
# 1. Delete o agente com force via API
TOKEN=$(gcloud auth print-access-token)
curl -X DELETE "https://us-west1-aiplatform.googleapis.com/v1/projects/SEU_PROJECT/locations/us-west1/reasoningEngines/ID?force=true" \
  -H "Authorization: Bearer $TOKEN"

# 2. Remova do state do Terraform
terraform state rm 'google_vertex_ai_reasoning_engine.agent["sentinel_ai_ubs_per_3km"]'

# 3. Reaplique para recriar
terraform apply -var="deploy_cloud_run=true"
```

O `deletion_policy = "FORCE"` já está configurado no `infra/agent_engine.tf` para que deletes futuros funcionem automaticamente.

### Vitta.AI: resposta demora muito (> 2 min)

Os agentes usam o Gemini 3.5 Flash via google-adk, realizando tool calls (Google Search) para responder. O tempo varia com a complexidade da query:
- Agente de Saúde (3 UBS por trajeto): 65–135s
- Agente UBS por 3km: 30–120s

O timeout interno do endpoint `/sentinel/ubs_raio_casa` é de **120s** — se excedido, retorna `{"qtd_ubs": null}` e o frontend mantém o valor padrão (1).

### Destruir recursos GCP (após avaliação)

```bash
cd infra
terraform destroy
```

---

## Notebooks e pipeline de dados

Os notebooks de análise exploratória e modelagem estão na raiz do repositório (`discovery/`, `src/`). O microserviço **prediction** encapsula o pipeline de treino; os dados de amostra estão em `data/raw/` (PNS 2019, OD 2017, GTFS SPTrans, GeoSampa UBS).

---

## Licença e uso acadêmico

Projeto desenvolvido como Trabalho de Conclusão de Curso (TCC) do MBA em Engenharia de Dados da FIAP, no contexto da disciplina Discovery com case Google.
