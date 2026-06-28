from app.clients.base import ServiceClient
from app.config import settings


storage_client = ServiceClient(settings.storage_service_url, "storage")
prediction_client = ServiceClient(settings.prediction_service_url, "prediction")
auth_client = ServiceClient(settings.auth_service_url, "auth")
