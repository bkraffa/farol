"""
Cliente para scraping do Facebook via Apify
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from apify_client import ApifyClient

logger = logging.getLogger(__name__)


class ApifyFacebookScraper:
    """Cliente para scraping de grupos do Facebook usando Apify"""
    
    def __init__(self, api_token: str):
        self.client = ApifyClient(api_token)
        self.actor_id = "apify/facebook-groups-scraper"
        
    def run_historical_scrape(
        self, 
        group_urls: List[str],
        days_back: int = 730  # 2 anos
    ) -> Dict[str, Any]:
        """
        Executa scraping histórico de posts antigos
        
        Args:
            group_urls: Lista de URLs dos grupos
            days_back: Número de dias para voltar (padrão: 730 = 2 anos)
            
        Returns:
            Dados do scraping e informações do job
        """
        logger.info(f"Iniciando scraping histórico de {len(group_urls)} grupos")
        logger.info(f"Buscando posts dos últimos {days_back} dias")
        
        run_input = {
            "startUrls": [{"url": url} for url in group_urls],
            "viewOption": "CHRONOLOGICAL",
            "onlyPostsNewerThan": f"{days_back} days",
            "maxPosts": 10000,  # Limite de segurança
            "resultsLimit": 10000
        }
        
        return self._run_scraper(run_input, "historical")
    
    def run_incremental_scrape(
        self,
        group_urls: List[str],
        hours_back: int = 12
    ) -> Dict[str, Any]:
        """
        Executa scraping incremental de posts recentes
        
        Args:
            group_urls: Lista de URLs dos grupos
            hours_back: Número de horas para voltar (padrão: 12)
            
        Returns:
            Dados do scraping e informações do job
        """
        logger.info(f"Iniciando scraping incremental de {len(group_urls)} grupos")
        logger.info(f"Buscando posts das últimas {hours_back} horas")
        
        run_input = {
            "startUrls": [{"url": url} for url in group_urls],
            "viewOption": "CHRONOLOGICAL",
            "onlyPostsNewerThan": f"{hours_back} hours",
            "maxPosts": 500,  # Menor limite para execuções frequentes
            "resultsLimit": 500
        }
        
        return self._run_scraper(run_input, "incremental")
    
    def _run_scraper(self, run_input: Dict, job_type: str) -> Dict[str, Any]:
        """
        Executa o scraper do Apify
        
        Args:
            run_input: Configuração do scraper
            job_type: Tipo do job (historical ou incremental)
            
        Returns:
            Dados do scraping
        """
        try:
            # Executar o actor
            logger.info(f"Executando Apify actor: {self.actor_id}")
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            
            # Obter resultados do dataset
            dataset_id = run["defaultDatasetId"]
            items = list(self.client.dataset(dataset_id).iterate_items())
            
            logger.info(f"Scraping concluído: {len(items)} posts coletados")
            
            return {
                "job_type": job_type,
                "run_id": run["id"],
                "status": run["status"],
                "started_at": run["startedAt"],
                "finished_at": run["finishedAt"],
                "stats": run.get("stats", {}),
                "items": items,
                "total_items": len(items)
            }
            
        except Exception as e:
            logger.error(f"Erro ao executar scraper: {str(e)}")
            raise
    
    def save_raw_data(self, data: Dict[str, Any], output_dir: str) -> str:
        """
        Salva dados brutos do scraping
        
        Args:
            data: Dados do scraping
            output_dir: Diretório de saída
            
        Returns:
            Caminho do arquivo salvo
        """
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        job_type = data["job_type"]
        filename = f"{job_type}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Dados salvos em: {filepath}")
        return filepath


def load_groups_config(config_path: str = "config/groups.json") -> List[str]:
    """
    Carrega configuração dos grupos do Facebook
    
    Args:
        config_path: Caminho para o arquivo de configuração
        
    Returns:
        Lista de URLs dos grupos ativos
    """
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return [
        group["url"] 
        for group in config["groups"] 
        if group.get("active", True)
    ]
