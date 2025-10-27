"""
Kitesurf Equipment Scraper & Analyzer
Sistema de scraping e análise inteligente de anúncios de kitesurfe
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from src.apify_scraper import ApifyFacebookScraper
from src.openai_analyzer import OpenAIAnalyzer
from src.data_processor import DataProcessor
from src.models import FacebookPost, EquipmentAd, EquipmentType, EquipmentCondition

__all__ = [
    "ApifyFacebookScraper",
    "OpenAIAnalyzer", 
    "DataProcessor",
    "FacebookPost",
    "EquipmentAd",
    "EquipmentType",
    "EquipmentCondition"
]
