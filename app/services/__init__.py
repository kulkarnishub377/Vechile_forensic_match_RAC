"""Services module initialization"""
from .ingestion_service import IngestionService, get_ingestion_service

__all__ = [
    'IngestionService',
    'get_ingestion_service'
]
