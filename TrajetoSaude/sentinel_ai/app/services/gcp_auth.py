"""
Gerencia o token de acesso ao GCP usando Application Default Credentials (ADC).

Como configurar (uma única vez por máquina):
    gcloud auth application-default login

O google-auth renova o token automaticamente antes de expirar.
"""

import google.auth
import google.auth.transport.requests

_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

_credentials = None
_http_request = google.auth.transport.requests.Request()


def get_access_token() -> str:
    """Retorna um token Bearer válido, renovando se necessário."""
    global _credentials
    if _credentials is None:
        _credentials, _ = google.auth.default(scopes=_SCOPES)
    if not _credentials.valid:
        _credentials.refresh(_http_request)
    return _credentials.token
