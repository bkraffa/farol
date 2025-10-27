"""
Data models para o sistema de scraping e análise
"""
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EquipmentType(str, Enum):
    """Tipos de equipamento de kitesurf"""
    KITE = "kite"
    BOARD = "board"
    BAR = "bar"
    HARNESS = "harness"
    WETSUIT = "wetsuit"
    PUMP = "pump"
    ACCESSORIES = "accessories"
    COMPLETE_SET = "complete_set"
    OTHER = "other"


class EquipmentCondition(str, Enum):
    """Condições do equipamento"""
    NEW = "novo"
    LIKE_NEW = "seminovo"
    GOOD = "bom_estado"
    USED = "usado"
    NEEDS_REPAIR = "precisa_reparo"
    UNKNOWN = "desconhecido"


@dataclass
class FacebookPost:
    """Dados brutos do post do Facebook"""
    post_id: str
    url: str
    time: str
    user_name: str
    text: str
    title: Optional[str]
    price: Optional[str]
    location: Optional[str]
    group_url: str
    group_title: str
    likes_count: int
    comments_count: int
    shares_count: int
    images: List[str]  # URLs das imagens
    comments: List[Dict[str, Any]]
    
    def to_dict(self):
        return asdict(self)


@dataclass
class EquipmentAd:
    """Dados estruturados de um anúncio de equipamento"""
    # Identificação
    post_id: str
    post_url: str
    scraped_at: str
    analyzed_at: str
    
    # Classificação
    is_advertisement: bool
    confidence_score: float  # 0-1
    
    # Equipamento
    equipment_type: str  # EquipmentType
    brand: Optional[str]
    model: Optional[str]
    year: Optional[int]
    size: Optional[str]  # ex: "12m", "136x41cm"
    condition: str  # EquipmentCondition
    has_repair: bool
    repair_description: Optional[str]
    
    # Preço e Localização
    price: Optional[float]
    currency: str = "BRL"
    price_negotiable: bool = False
    city: Optional[str]
    state: Optional[str]  # Sigla (CE, SP, RJ, etc)
    
    # Informações Adicionais
    description: str
    additional_items: List[str]  # Itens extras incluídos
    contact_info: Optional[str]
    contact_preferences: List[str]  # WhatsApp, telefone, etc
    
    # Origem dos dados
    extracted_from_text: bool
    extracted_from_images: bool
    extracted_from_comments: bool
    
    # Análise
    analysis_notes: Optional[str]
    keywords: List[str]
    
    # Dados do vendedor
    seller_name: str
    seller_profile_url: Optional[str]
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_analysis(cls, post: FacebookPost, analysis: Dict[str, Any]) -> 'EquipmentAd':
        """Cria um EquipmentAd a partir da análise da OpenAI"""
        return cls(
            post_id=post.post_id,
            post_url=post.url,
            scraped_at=post.time,
            analyzed_at=datetime.utcnow().isoformat(),
            is_advertisement=analysis.get('is_advertisement', False),
            confidence_score=analysis.get('confidence_score', 0.0),
            equipment_type=analysis.get('equipment_type', EquipmentType.OTHER.value),
            brand=analysis.get('brand'),
            model=analysis.get('model'),
            year=analysis.get('year'),
            size=analysis.get('size'),
            condition=analysis.get('condition', EquipmentCondition.UNKNOWN.value),
            has_repair=analysis.get('has_repair', False),
            repair_description=analysis.get('repair_description'),
            price=analysis.get('price'),
            currency=analysis.get('currency', 'BRL'),
            price_negotiable=analysis.get('price_negotiable', False),
            city=analysis.get('city'),
            state=analysis.get('state'),
            description=analysis.get('description', post.text),
            additional_items=analysis.get('additional_items', []),
            contact_info=analysis.get('contact_info'),
            contact_preferences=analysis.get('contact_preferences', []),
            extracted_from_text=analysis.get('extracted_from_text', True),
            extracted_from_images=analysis.get('extracted_from_images', len(post.images) > 0),
            extracted_from_comments=analysis.get('extracted_from_comments', len(post.comments) > 0),
            analysis_notes=analysis.get('analysis_notes'),
            keywords=analysis.get('keywords', []),
            seller_name=post.user_name,
            seller_profile_url=None
        )


@dataclass
class ScrapingJob:
    """Configuração de um job de scraping"""
    job_id: str
    job_type: str  # "historical" ou "incremental"
    start_time: str
    end_time: Optional[str]
    status: str
    groups: List[str]
    posts_scraped: int
    posts_analyzed: int
    errors: List[str]
    
    def to_dict(self):
        return asdict(self)
