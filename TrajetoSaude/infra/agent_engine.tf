# Vertex AI Agent Engine (Reasoning Engines) — agentes Sentinel.AI
#
# Código-fonte em infra/agents/<nome>/agent.py (ADK puro, entrypoint
# `root_agent`). Empacotado em infra/agents/<nome>/source.tar.gz.b64 via
# infra/scripts/package-agents.sh e enviado inline (sem bucket GCS) através
# de source_code_spec.inline_source.
#
# Para atualizar um agente: edite agent.py, rode o script de empacotamento
# e então terraform apply.

variable "reasoning_engine_region" {
     description = "Região do Vertex AI Agent Engine (Reasoning Engines). gemini-3.x hoje só está disponível em algumas regiões."
     type        = string
     default     = "us-west1"
}

locals {
     agent_engines = {
          sentinela_ai = {
               display_name = "sentinela-ai-paciente"
               description  = "Assistente que ajuda o paciente a encontrar hubs de saúde para atendimento rápido."
          }
          sentinela_ai_agentedesaude = {
               display_name = "sentinela-ai-agente-de-saude"
               description  = "Agente de indicação de UBS mais próximas da rota de trabalho do paciente."
          }
          sentinel_ai_ubs_per_3km = {
               display_name = "sentinel-ai-ubs-per-3km"
               description  = "Calcula a quantidade de UBS num raio de 3km de um endereço."
          }
     }

     # Métodos expostos pelo runtime padrão do ADK ao envolver um root_agent.
     agent_class_methods = jsonencode([
          { name = "create_session",     api_mode = "" },
          { name = "get_session",        api_mode = "" },
          { name = "list_sessions",      api_mode = "" },
          { name = "delete_session",     api_mode = "" },
          { name = "stream_query",       api_mode = "stream" },
          { name = "async_stream_query", api_mode = "stream" },
     ])
}

resource "google_vertex_ai_reasoning_engine" "agent" {
     for_each        = local.agent_engines
     project         = var.project_id
     region          = var.reasoning_engine_region
     display_name    = each.value.display_name
     description     = each.value.description
     deletion_policy = "FORCE"

     spec {
          agent_framework = "google-adk"
          service_account = google_service_account.app.email
          class_methods   = local.agent_class_methods

          source_code_spec {
               inline_source {
                    source_archive = trimspace(file("${path.module}/agents/${each.key}/source.tar.gz.b64"))
               }

               python_spec {
                    entrypoint_module = "agent"
                    entrypoint_object = "agent_engine"
                    requirements_file = "requirements.txt"
                    version           = "3.12"
               }
          }
     }

     depends_on = [google_project_service.apis, google_project_iam_member.app_vertex]
}

locals {
     agent_engine_query_urls = {
          for k, v in google_vertex_ai_reasoning_engine.agent :
          k => "https://${var.reasoning_engine_region}-aiplatform.googleapis.com/v1/${v.id}:streamQuery"
     }
}

output "agent_engine_resource_names" {
     description = "Resource names (projects/.../reasoningEngines/ID) dos agentes criados."
     value        = { for k, v in google_vertex_ai_reasoning_engine.agent : k => v.id }
}

output "agent_engine_query_urls" {
     description = "URLs de streamQuery para cada agente, prontas para uso no sentinel_ai."
     value        = local.agent_engine_query_urls
}
