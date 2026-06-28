"""
Serviço de indicação de hubs de saúde e UBS próximas ao paciente.

Os dados são mockados com unidades reais de São Paulo ao longo das
principais linhas de transporte (Metrô/CPTM), refletindo a lógica
do Trajeto Saúde: encontrar o cuidado no caminho do trabalhador.
"""

from app.schemas.hubs import Hub

# Diretório de hubs — indexado por regiões atendidas
_DIRETORIO: list[dict] = [
    {
        "nome": "UBS Jardim Ipanema",
        "endereco": "Rua das Acácias, 210 — Jardim Ipanema",
        "distancia_min": 14,
        "regioes": ["Jardim Ipanema"],
        "tipo": "ubs",
    },
    {
        "nome": "Hub de Saúde — Terminal Barra Funda",
        "endereco": "Av. Auro Soares de Moura Andrade, 564 — Barra Funda",
        "distancia_min": 19,
        "regioes": ["Vila Esperança", "Barra Funda", "Santa Cecília"],
        "tipo": "hub",
    },
    {
        "nome": "UBS Vila Esperança",
        "endereco": "Av. Brasil, 880 — Vila Esperança",
        "distancia_min": 22,
        "regioes": ["Vila Esperança"],
        "tipo": "ubs",
    },
    {
        "nome": "Hub de Saúde — Terminal da Luz",
        "endereco": "Praça da Luz, s/n — Luz",
        "distancia_min": 24,
        "regioes": ["Centro", "Luz", "República", "Sé"],
        "tipo": "hub",
    },
    {
        "nome": "Hub de Saúde — Terminal Pirituba",
        "endereco": "Av. Coronel Sezefredo Fagundes, s/n — Pirituba",
        "distancia_min": 28,
        "regioes": ["Pirituba", "Jaraguá", "Perus"],
        "tipo": "hub",
    },
    {
        "nome": "Hub de Saúde — Terminal Pinheiros",
        "endereco": "Rua Deputado Lacerda Franco, 300 — Pinheiros",
        "distancia_min": 30,
        "regioes": ["Pinheiros", "Itaim Bibi", "Vila Madalena"],
        "tipo": "hub",
    },
    {
        "nome": "UBS Parque das Flores",
        "endereco": "Rua dos Lírios, 75 — Parque das Flores",
        "distancia_min": 35,
        "regioes": ["Parque das Flores"],
        "tipo": "ubs",
    },
    {
        "nome": "Hub de Saúde — Terminal Santana",
        "endereco": "Av. Cruzeiro do Sul, 1500 — Santana",
        "distancia_min": 32,
        "regioes": ["Santana", "Tucuruvi", "Mandaqui"],
        "tipo": "hub",
    },
    {
        "nome": "Hub de Saúde — Terminal Santo André (ABC)",
        "endereco": "Av. Industrial, 600 — Santo André",
        "distancia_min": 40,
        "regioes": ["Santo André", "São Bernardo", "São Caetano"],
        "tipo": "hub",
    },
]


def _normalizar(texto: str) -> str:
    return texto.strip().lower()


def hubs_proximos(bairro: str, rota_trabalho: list[str]) -> list[Hub]:
    """
    Retorna os hubs ordenados por:
    1. Hubs no bairro do paciente ou no trajeto (no_trajeto=True) primeiro
    2. Distância crescente como critério de desempate
    """
    regioes_paciente = {_normalizar(r) for r in [bairro, *rota_trabalho]}

    resultado: list[Hub] = []
    for h in _DIRETORIO:
        regioes_hub = {_normalizar(r) for r in h["regioes"]}
        no_trajeto = bool(regioes_hub & regioes_paciente)
        resultado.append(Hub(
            nome=h["nome"],
            endereco=h["endereco"],
            distancia_min=h["distancia_min"],
            no_trajeto=no_trajeto,
            tipo=h["tipo"],
        ))

    resultado.sort(key=lambda h: (not h.no_trajeto, h.distancia_min))
    return resultado
