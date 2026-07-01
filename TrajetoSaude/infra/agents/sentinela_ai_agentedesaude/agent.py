from functools import cached_property

from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.genai import Client
from google.adk.tools import agent_tool
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.adk.tools import url_context



class GlobalGemini(Gemini):
  """Pins the Vertex AI client to the `global` location.

  gemini-3 series models are only served from `global`; the default ADK
  `Gemini` integration constructs a `google.genai.Client` whose location
  defaults to the AgentEngine instance's region (e.g. `us-central1`) and
  fails with model-not-found for these models. Subclassing per the override
  pattern documented on `google.adk.models.google_llm.Gemini` lets the agent
  keep running in its regional AgentEngine instance while routing the model
  request to the global endpoint.
  """

  @cached_property
  def api_client(self) -> Client:
    return Client(vertexai=True, location="global")


sentinela_ai_agentedesaude_google_search_agent = LlmAgent(
  name='sentinela_ai_agentedesaude_google_search_agent',
  model=GlobalGemini(model='gemini-3.5-flash'),
  description=(
      'Agent specialized in performing Google searches.'
  ),
  sub_agents=[],
  instruction='Use the GoogleSearchTool to find information on the web.',
  tools=[
    GoogleSearchTool()
  ],
)
sentinela_ai_agentedesaude_url_context_agent = LlmAgent(
  name='sentinela_ai_agentedesaude_url_context_agent',
  model=GlobalGemini(model='gemini-3.5-flash'),
  description=(
      'Agent specialized in fetching content from URLs.'
  ),
  sub_agents=[],
  instruction='Use the UrlContextTool to retrieve content from provided URLs.',
  tools=[
    url_context
  ],
)
root_agent = LlmAgent(
  name='sentinela_ai_agentedesaude',
  model=GlobalGemini(model='gemini-3.5-flash'),
  description=(
      'Agente de indicação de UBS mais próximas da rota de trabalho do paciente'
  ),
  sub_agents=[],
  instruction='Você é o agente SentinelaAI, especializado em apoiar profissionais de saúde (médicos, enfermeiros, agentes comunitários) na orientação de pacientes sobre o acesso às Unidades Básicas de Saúde (UBS) em São Paulo.\n\nSua função é indicar **3 opções de UBS** com base em diferentes pontos de referência do paciente:\n1. Uma UBS próxima ao **hub de atendimento atual**.\n2. Uma UBS próxima ao **endereço de trabalho** do paciente.\n3. Uma UBS próxima à **residência** do paciente.\n\nPara obter os dados das UBS, você deve consultar  o seguinte site:\nhttps://drive.prefeitura.sp.gov.br/cidade/secretarias/upload/2024_05_08_Relacao_da_UBS_da_Cidade_de_Sao_Paulo.pdf\n\n\n### Regras de resposta:\n- Sempre apresentar **3 sugestões distintas** (uma para cada ponto de referência).\n- Para cada sugestão, indicar:\n  - Nome da UBS\n  - Endereço completo\n  - Distância aproximada em relação ao ponto de referência\n  - Justificativa breve de por que aquela UBS é a melhor opção para o local indicado\n- Finalizar recomendando a **melhor escolha** para cada endereço, destacando praticidade e acessibilidade.\n\n### Objetivo:\nFacilitar a tomada de decisão do paciente e do profissional de saúde, garantindo que o paciente tenha acesso rápido e eficiente à UBS mais adequada para sua rotina.\n\n\nretorne em formato json\ncom o seguinte payload:\n\n{\n   \"items\":[ \n        {\n          \"name:\":\"...\",\n          \"description\":\"\",\n          \"address\":\"...\",\n          \"cep:\"\"\"\n         }\n]\n}',
  tools=[
    agent_tool.AgentTool(agent=sentinela_ai_agentedesaude_google_search_agent),
    agent_tool.AgentTool(agent=sentinela_ai_agentedesaude_url_context_agent)
  ],
)
# Wrapper necessário para o Vertex AI Agent Engine expor os métodos
# de sessão e streaming (create_session, async_stream_query, etc.)
from vertexai.agent_engines import AdkApp
agent_engine = AdkApp(agent=root_agent)
