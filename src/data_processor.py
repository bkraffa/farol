"""
Processador de dados - integra scraping, análise e persistência
"""
import os
import json
import logging
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
from src.models import FacebookPost, EquipmentAd
from src.database import MongoDBPersistence

logger = logging.getLogger(__name__)


class DataProcessor:
    """Processa e organiza dados com MongoDB"""
    
    def __init__(self, use_mongodb: bool = True, data_dir: str = "data"):
        self.use_mongodb = use_mongodb
        self.data_dir = data_dir
        self.backup_dir = os.path.join(data_dir, "backups")
        
        # Criar diretório de backup
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Inicializar MongoDB
        if use_mongodb:
            self.db = MongoDBPersistence()
            logger.info("✓ DataProcessor usando MongoDB")
        else:
            self.db = None
            logger.info("⚠️  DataProcessor SEM MongoDB (modo legacy)")
    
    def process_raw_scraping(self, raw_data: Dict[str, Any]) -> List[FacebookPost]:
        """
        Processa dados brutos do Apify em objetos FacebookPost
        
        Args:
            raw_data: Dados brutos do scraping
            
        Returns:
            Lista de FacebookPost
        """
        posts = []
        items = raw_data.get("items", [])
        
        logger.info(f"Processando {len(items)} posts brutos")
        
        for item in items:
            try:
                # Pegar dados do sharedPost se existir
                if "sharedPost" in item and item["sharedPost"]:
                    shared = item["sharedPost"]
                    text = shared.get("text", "")
                    title = shared.get("title", "")
                    location = shared.get("location", "")
                    price = shared.get("price", "")
                    attachments = shared.get("attachments", [])
                else:
                    text = item.get("text", "")
                    title = item.get("title", "")
                    location = item.get("location", "")
                    price = item.get("price", "")
                    attachments = item.get("attachments", [])
                
                # Extrair URLs de imagens
                image_urls = []
                for att in attachments:
                    if att.get("__typename") == "Photo":
                        if "photo_image" in att:
                            image_urls.append(att["photo_image"]["uri"])
                        elif "image" in att:
                            image_urls.append(att["image"]["uri"])
                
                # Extrair comentários
                comments = []
                for comment in item.get("topComments", [])[:10]:
                    if "text" in comment:
                        comments.append({
                            "text": comment["text"],
                            "author": comment.get("author", {}).get("name", "Unknown")
                        })
                
                post = FacebookPost(
                    post_id=item.get("id") or item.get("legacyId", "unknown"),
                    url=item.get("url", ""),
                    time=item.get("time", ""),
                    user_name=item.get("user", {}).get("name", "Unknown"),
                    text=text,
                    title=title,
                    price=price,
                    location=location,
                    group_url=item.get("facebookUrl", ""),
                    group_title=item.get("groupTitle", "Unknown Group"),
                    likes_count=item.get("likesCount", 0),
                    comments_count=item.get("commentsCount", 0),
                    shares_count=item.get("sharesCount", 0),
                    images=image_urls,
                    comments=comments
                )
                
                posts.append(post)
                
            except Exception as e:
                logger.error(f"Erro ao processar item: {str(e)}")
                continue
        
        logger.info(f"✓ {len(posts)} posts processados")
        
        # Salvar no MongoDB se habilitado
        if self.db:
            self.db.save_raw_posts(posts)
        
        return posts
    
    def create_equipment_ads(
        self,
        posts: List[FacebookPost],
        analyses: List[Dict[str, Any]]
    ) -> List[EquipmentAd]:
        """
        Cria objetos EquipmentAd e salva no MongoDB
        
        Args:
            posts: Lista de posts processados
            analyses: Lista de análises da OpenAI
            
        Returns:
            Lista de EquipmentAd
        """
        ads = []
        
        for post, analysis in zip(posts, analyses):
            try:
                ad = EquipmentAd.from_analysis(post, analysis)
                ads.append(ad)
            except Exception as e:
                logger.error(f"Erro ao criar EquipmentAd: {str(e)}")
                continue
        
        # Filtrar apenas anúncios verdadeiros
        true_ads = [ad for ad in ads if ad.is_advertisement]
        
        logger.info(
            f"✓ {len(true_ads)} anúncios de {len(ads)} posts analisados"
        )
        
        # Salvar no MongoDB se habilitado
        if self.db:
            self.db.save_equipment_ads(true_ads)
        
        return true_ads
    
    def save_backup(
        self,
        ads: List[EquipmentAd],
        job_type: str = "incremental"
    ) -> Dict[str, str]:
        """
        Salva backup em JSON/CSV (além do MongoDB)
        
        Args:
            ads: Lista de anúncios
            job_type: Tipo do job
            
        Returns:
            Dicionário com caminhos dos arquivos
        """
        if not ads:
            logger.warning("Nenhum anúncio para fazer backup")
            return {}
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{job_type}_{timestamp}"
        
        # Converter para dicionários
        ads_data = [ad.to_dict() for ad in ads]
        
        # Salvar JSON
        json_path = os.path.join(self.backup_dir, f"{base_filename}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(ads_data, f, ensure_ascii=False, indent=2)
        
        # Salvar CSV resumido
        csv_path = os.path.join(self.backup_dir, f"{base_filename}.csv")
        df = pd.DataFrame(ads_data)
        
        # Colunas principais para CSV
        main_cols = [
            'post_id', 'equipment_type', 'brand', 'model', 'year', 
            'size', 'price', 'condition', 'city', 'state', 
            'has_repair', 'confidence_score', 'post_url'
        ]
        existing_cols = [col for col in main_cols if col in df.columns]
        df_summary = df[existing_cols]
        df_summary.to_csv(csv_path, index=False, encoding='utf-8')
        
        logger.info(f"✓ Backup salvo:")
        logger.info(f"  - JSON: {json_path}")
        logger.info(f"  - CSV: {csv_path}")
        
        return {
            "json": json_path,
            "csv": csv_path
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Gera estatísticas (do MongoDB ou dados locais)
        
        Returns:
            Dicionário com estatísticas
        """
        if self.db:
            # Usar estatísticas do MongoDB
            return self.db.get_statistics()
        else:
            # Modo legacy sem MongoDB
            logger.warning("MongoDB não disponível, estatísticas limitadas")
            return {"total_ads": 0}
    
    def search_ads(self, **filters) -> List[Dict]:
        """
        Busca anúncios com filtros
        
        Args:
            **filters: Filtros de busca (brand, equipment_type, etc)
            
        Returns:
            Lista de anúncios
        """
        if not self.db:
            logger.error("MongoDB não disponível")
            return []
        
        return self.db.search_ads(**filters)
    
    def get_recent_ads(self, hours: int = 24) -> List[Dict]:
        """
        Busca anúncios recentes
        
        Args:
            hours: Últimas X horas
            
        Returns:
            Lista de anúncios
        """
        if not self.db:
            logger.error("MongoDB não disponível")
            return []
        
        return self.db.get_recent_ads(hours=hours)
    
    def export_to_csv(self, output_file: str, query: Dict = None):
        """
        Exporta dados do MongoDB para CSV
        
        Args:
            output_file: Caminho do arquivo
            query: Query opcional
        """
        if not self.db:
            logger.error("MongoDB não disponível")
            return
        
        self.db.export_to_csv(output_file, query)
    
    def close(self):
        """Fecha conexões"""
        if self.db:
            self.db.close()
