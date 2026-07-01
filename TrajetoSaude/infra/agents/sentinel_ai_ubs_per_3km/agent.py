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


sentinel_ai_ubs_per_3km_google_search_agent = LlmAgent(
  name='sentinel_ai_ubs_per_3km_google_search_agent',
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
sentinel_ai_ubs_per_3km_url_context_agent = LlmAgent(
  name='sentinel_ai_ubs_per_3km_url_context_agent',
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
  name='sentinel_ai_ubs_per_3km',
  model=GlobalGemini(model='gemini-3.5-flash'),
  description=(
      'Você é uma gente que ajuda a identificar quantas ubs (unidade basica de saude) tem perto de um endereço dentro da cidade de SP'
  ),
  sub_agents=[],
  instruction='Dado um endereço específico, \nCalcule quantas UBS (unidade básica de saúde) estão localizadas perto desse endereco no máximo 3 ubs. consulte o Google.\n\nResponda rapidamente, sem pesquisas adicionais além do necessário. Retorne APENAS um JSON no formato:\n\n{\n  "qtd_ubs": <número inteiro>\n}',
  tools=[
    agent_tool.AgentTool(agent=sentinel_ai_ubs_per_3km_google_search_agent),
    agent_tool.AgentTool(agent=sentinel_ai_ubs_per_3km_url_context_agent)
  ],
)
# Wrapper necessário para o Vertex AI Agent Engine expor os métodos
# de sessão e streaming (create_session, async_stream_query, etc.)
from vertexai.agent_engines import AdkApp
agent_engine = AdkApp(agent=root_agent)
