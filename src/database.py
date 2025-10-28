"""
Camada de persistência com MongoDB
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from src.models import FacebookPost, EquipmentAd

logger = logging.getLogger(__name__)


class MongoDBPersistence:
    """Gerenciador de persistência MongoDB"""
    
    def __init__(self, connection_string: str = None, database_name: str = "kitesurf"):
        """
        Inicializa conexão com MongoDB
        
        Args:
            connection_string: URI de conexão (MongoDB Atlas ou local)
            database_name: Nome do database
        """
        self.connection_string = connection_string or os.getenv(
            "MONGODB_URI", 
            "mongodb://localhost:27017/"
        )
        self.database_name = database_name
        
        try:
            self.client = MongoClient(self.connection_string)
            # Testar conexão
            self.client.admin.command('ping')
            self.db = self.client[database_name]
            
            # Criar índices
            self._create_indexes()
            
            logger.info(f"✓ Conectado ao MongoDB: {database_name}")
            
        except ConnectionFailure as e:
            logger.error(f"Erro ao conectar no MongoDB: {str(e)}")
            raise
    
    def _create_indexes(self):
        """Cria índices otimizados"""
        
        # Collection: raw_posts
        self.db.raw_posts.create_index([("post_id", ASCENDING)], unique=True)
        self.db.raw_posts.create_index([("scraped_at", DESCENDING)])
        self.db.raw_posts.create_index([("group_url", ASCENDING)])
        
        # Collection: equipment_ads
        self.db.equipment_ads.create_index([("post_id", ASCENDING)], unique=True)
        self.db.equipment_ads.create_index([("analyzed_at", DESCENDING)])
        self.db.equipment_ads.create_index([("is_advertisement", ASCENDING)])
        self.db.equipment_ads.create_index([("equipment_type", ASCENDING)])
        self.db.equipment_ads.create_index([("brand", ASCENDING)])
        self.db.equipment_ads.create_index([("state", ASCENDING)])
        self.db.equipment_ads.create_index([("price", ASCENDING)])
        self.db.equipment_ads.create_index([("resale_score", DESCENDING)])  # NOVO
        
        # Índice composto para queries comuns
        self.db.equipment_ads.create_index([
            ("is_advertisement", ASCENDING),
            ("equipment_type", ASCENDING),
            ("brand", ASCENDING)
        ])
        
        # Índice de texto para busca full-text
        self.db.equipment_ads.create_index([
            ("description", "text"),
            ("brand", "text"),
            ("model", "text")
        ])
        
        logger.info("✓ Índices criados")
    
    def save_raw_posts(self, posts: List[FacebookPost]) -> int:
        """
        Salva posts brutos
        
        Args:
            posts: Lista de FacebookPost
            
        Returns:
            Número de posts salvos
        """
        if not posts:
            return 0
        
        saved = 0
        for post in posts:
            try:
                doc = post.to_dict()
                doc['scraped_at'] = datetime.utcnow()
                
                # Upsert (insert ou update se já existe)
                self.db.raw_posts.update_one(
                    {'post_id': post.post_id},
                    {'$set': doc},
                    upsert=True
                )
                saved += 1
                
            except DuplicateKeyError:
                logger.debug(f"Post {post.post_id} já existe")
            except Exception as e:
                logger.error(f"Erro ao salvar post {post.post_id}: {str(e)}")
        
        logger.info(f"✓ {saved} posts salvos no MongoDB")
        return saved
    
    def save_equipment_ads(self, ads: List[EquipmentAd]) -> int:
        """
        Salva anúncios analisados
        
        Args:
            ads: Lista de EquipmentAd
            
        Returns:
            Número de anúncios salvos
        """
        if not ads:
            return 0
        
        saved = 0
        for ad in ads:
            try:
                doc = ad.to_dict()
                doc['analyzed_at'] = datetime.utcnow()
                
                # Upsert
                self.db.equipment_ads.update_one(
                    {'post_id': ad.post_id},
                    {'$set': doc},
                    upsert=True
                )
                saved += 1
                
            except DuplicateKeyError:
                logger.debug(f"Anúncio {ad.post_id} já existe")
            except Exception as e:
                logger.error(f"Erro ao salvar anúncio {ad.post_id}: {str(e)}")
        
        logger.info(f"✓ {saved} anúncios salvos no MongoDB")
        return saved
    
    def get_unanalyzed_posts(self, limit: int = 100) -> List[Dict]:
        """
        Busca posts que ainda não foram analisados
        
        Args:
            limit: Número máximo de posts
            
        Returns:
            Lista de posts não analisados
        """
        # Posts que não estão em equipment_ads
        analyzed_ids = set(
            doc['post_id'] 
            for doc in self.db.equipment_ads.find({}, {'post_id': 1})
        )
        
        posts = list(
            self.db.raw_posts.find({
                'post_id': {'$nin': list(analyzed_ids)}
            }).limit(limit)
        )
        
        logger.info(f"Encontrados {len(posts)} posts não analisados")
        return posts
    
    def search_ads(
        self,
        equipment_type: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        state: Optional[str] = None,
        has_repair: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Busca anúncios com filtros
        
        Args:
            equipment_type: Tipo de equipamento
            brand: Marca
            min_price: Preço mínimo
            max_price: Preço máximo
            state: Estado (sigla)
            has_repair: Tem reparo?
            limit: Limite de resultados
            
        Returns:
            Lista de anúncios
        """
        query = {'is_advertisement': True}
        
        if equipment_type:
            query['equipment_type'] = equipment_type
        
        if brand:
            query['brand'] = {'$regex': brand, '$options': 'i'}
        
        if min_price is not None or max_price is not None:
            query['price'] = {}
            if min_price is not None:
                query['price']['$gte'] = min_price
            if max_price is not None:
                query['price']['$lte'] = max_price
        
        if state:
            query['state'] = state.upper()
        
        if has_repair is not None:
            query['has_repair'] = has_repair
        
        ads = list(
            self.db.equipment_ads
            .find(query)
            .sort('analyzed_at', DESCENDING)
            .limit(limit)
        )
        
        logger.info(f"Busca retornou {len(ads)} anúncios")
        return ads
    
    def get_recent_ads(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """
        Busca anúncios recentes
        
        Args:
            hours: Últimas X horas
            limit: Limite de resultados
            
        Returns:
            Lista de anúncios recentes
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        ads = list(
            self.db.equipment_ads
            .find({
                'is_advertisement': True,
                'analyzed_at': {'$gte': cutoff}
            })
            .sort('analyzed_at', DESCENDING)
            .limit(limit)
        )
        
        logger.info(f"{len(ads)} anúncios nas últimas {hours} horas")
        return ads
    
    def get_high_potential_ads(
        self,
        min_score: int = 70,
        equipment_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Busca anúncios com alto potencial de revenda
        
        Args:
            min_score: Score mínimo (0-100)
            equipment_type: Filtrar por tipo
            limit: Limite de resultados
            
        Returns:
            Lista de anúncios com alto potencial
        """
        query = {
            'is_advertisement': True,
            'resale_score': {'$gte': min_score}
        }
        
        if equipment_type:
            query['equipment_type'] = equipment_type
        
        ads = list(
            self.db.equipment_ads
            .find(query)
            .sort('resale_score', DESCENDING)
            .limit(limit)
        )
        
        logger.info(f"{len(ads)} anúncios com score ≥ {min_score}")
        return ads
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Gera estatísticas do banco de dados
        
        Returns:
            Dicionário com estatísticas
        """
        stats = {}
        
        # Total de documentos
        stats['total_raw_posts'] = self.db.raw_posts.count_documents({})
        stats['total_ads'] = self.db.equipment_ads.count_documents({
            'is_advertisement': True
        })
        
        # Agregações
        pipeline = [
            {'$match': {'is_advertisement': True}},
            {'$group': {
                '_id': '$equipment_type',
                'count': {'$sum': 1},
                'avg_price': {'$avg': '$price'}
            }}
        ]
        
        stats['by_equipment_type'] = {
            doc['_id']: {
                'count': doc['count'],
                'avg_price': doc.get('avg_price')
            }
            for doc in self.db.equipment_ads.aggregate(pipeline)
        }
        
        # Top marcas
        pipeline = [
            {'$match': {'is_advertisement': True, 'brand': {'$ne': None}}},
            {'$group': {'_id': '$brand', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        
        stats['top_brands'] = [
            {'brand': doc['_id'], 'count': doc['count']}
            for doc in self.db.equipment_ads.aggregate(pipeline)
        ]
        
        # Por estado
        pipeline = [
            {'$match': {'is_advertisement': True, 'state': {'$ne': None}}},
            {'$group': {'_id': '$state', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        
        stats['by_state'] = {
            doc['_id']: doc['count']
            for doc in self.db.equipment_ads.aggregate(pipeline)
        }
        
        # Preços
        pipeline = [
            {'$match': {'is_advertisement': True, 'price': {'$ne': None}}},
            {'$group': {
                '_id': None,
                'avg': {'$avg': '$price'},
                'min': {'$min': '$price'},
                'max': {'$max': '$price'},
                'median': {'$push': '$price'}
            }}
        ]
        
        price_stats = list(self.db.equipment_ads.aggregate(pipeline))
        if price_stats:
            ps = price_stats[0]
            prices = sorted(ps['median'])
            median = prices[len(prices)//2] if prices else None
            
            stats['prices'] = {
                'avg': ps.get('avg'),
                'min': ps.get('min'),
                'max': ps.get('max'),
                'median': median
            }
        
        # Anúncios com reparo
        stats['with_repair'] = self.db.equipment_ads.count_documents({
            'is_advertisement': True,
            'has_repair': True
        })
        
        # Estatísticas de potencial de revenda (NOVO)
        pipeline_resale = [
            {'$match': {
                'is_advertisement': True,
                'resale_score': {'$ne': None}
            }},
            {'$group': {
                '_id': None,
                'avg_score': {'$avg': '$resale_score'},
                'min_score': {'$min': '$resale_score'},
                'max_score': {'$max': '$resale_score'},
                'high_potential': {
                    '$sum': {'$cond': [{'$gte': ['$resale_score', 70]}, 1, 0]}
                },
                'medium_potential': {
                    '$sum': {'$cond': [
                        {'$and': [
                            {'$gte': ['$resale_score', 50]},
                            {'$lt': ['$resale_score', 70]}
                        ]}, 1, 0
                    ]}
                },
                'low_potential': {
                    '$sum': {'$cond': [{'$lt': ['$resale_score', 50]}, 1, 0]}
                }
            }}
        ]
        
        resale_stats = list(self.db.equipment_ads.aggregate(pipeline_resale))
        if resale_stats:
            rs = resale_stats[0]
            stats['resale_potential'] = {
                'avg_score': round(rs.get('avg_score', 0), 1),
                'min_score': rs.get('min_score', 0),
                'max_score': rs.get('max_score', 0),
                'high_potential': rs.get('high_potential', 0),  # ≥70
                'medium_potential': rs.get('medium_potential', 0),  # 50-69
                'low_potential': rs.get('low_potential', 0)  # <50
            }
        
        return stats
    
    def text_search(self, search_text: str, limit: int = 50) -> List[Dict]:
        """
        Busca por texto (full-text search)
        
        Args:
            search_text: Texto a buscar
            limit: Limite de resultados
            
        Returns:
            Lista de anúncios
        """
        ads = list(
            self.db.equipment_ads
            .find(
                {'$text': {'$search': search_text}},
                {'score': {'$meta': 'textScore'}}
            )
            .sort([('score', {'$meta': 'textScore'})])
            .limit(limit)
        )
        
        logger.info(f"Busca por '{search_text}' retornou {len(ads)} resultados")
        return ads
    
    def export_to_csv(self, output_file: str, query: Dict = None):
        """
        Exporta dados para CSV (backup/análise)
        
        Args:
            output_file: Caminho do arquivo CSV
            query: Query opcional para filtrar
        """
        import pandas as pd
        
        if query is None:
            query = {'is_advertisement': True}
        
        ads = list(self.db.equipment_ads.find(query))
        
        if ads:
            df = pd.DataFrame(ads)
            # Remover _id do MongoDB
            if '_id' in df.columns:
                df = df.drop('_id', axis=1)
            
            df.to_csv(output_file, index=False, encoding='utf-8')
            logger.info(f"✓ {len(ads)} anúncios exportados para {output_file}")
        else:
            logger.warning("Nenhum anúncio para exportar")
    
    def close(self):
        """Fecha conexão com MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Conexão MongoDB fechada")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Funções auxiliares

def get_db() -> MongoDBPersistence:
    """Retorna instância do banco de dados"""
    return MongoDBPersistence()


def init_database():
    """
    Inicializa o banco de dados
    Cria índices e collections necessárias
    """
    logger.info("Inicializando banco de dados...")
    
    with get_db() as db:
        # Collections são criadas automaticamente
        # Índices são criados no __init__
        
        stats = db.get_statistics()
        logger.info(f"Banco inicializado:")
        logger.info(f"  - Posts brutos: {stats['total_raw_posts']}")
        logger.info(f"  - Anúncios: {stats['total_ads']}")
    
    logger.info("✓ Banco de dados pronto")
