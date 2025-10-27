#!/usr/bin/env python3
"""
Script para scraping incremental (últimas 12 horas)
Deve ser executado 2x por dia (8h e 20h)
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.apify_scraper import ApifyFacebookScraper, load_groups_config
from src.openai_analyzer import OpenAIAnalyzer
from src.data_processor import DataProcessor

# Configurar logging
log_dir = root_dir / "logs"
log_dir.mkdir(exist_ok=True)

timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"incremental_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Executa scraping incremental"""
    logger.info("=" * 80)
    logger.info("INICIANDO SCRAPING INCREMENTAL (12 HORAS)")
    logger.info("=" * 80)
    
    start_time = datetime.utcnow()
    
    try:
        # Carregar variáveis de ambiente
        env_path = root_dir / "config" / ".env"
        load_dotenv(env_path)
        
        apify_token = os.getenv("APIFY_API_TOKEN")
        openai_key = os.getenv("OPENAI_API_KEY")
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if not apify_token or not openai_key:
            raise ValueError(
                "APIFY_API_TOKEN e OPENAI_API_KEY devem estar definidos no .env"
            )
        
        # Carregar configuração dos grupos
        config_path = root_dir / "config" / "groups.json"
        group_urls = load_groups_config(str(config_path))
        
        logger.info(f"Grupos configurados: {len(group_urls)}")
        
        # Inicializar componentes
        scraper = ApifyFacebookScraper(apify_token)
        analyzer = OpenAIAnalyzer(openai_key, openai_model)
        processor = DataProcessor(str(root_dir / "data"))
        
        # 1. SCRAPING
        logger.info("\n" + "=" * 80)
        logger.info("FASE 1: SCRAPING DO FACEBOOK")
        logger.info("=" * 80)
        
        scraping_result = scraper.run_incremental_scrape(
            group_urls=group_urls,
            hours_back=12
        )
        
        total_posts = scraping_result["total_items"]
        logger.info(f"✓ Scraping concluído: {total_posts} posts coletados")
        
        if total_posts == 0:
            logger.info("Nenhum post novo encontrado. Finalizando.")
            return 0
        
        # Salvar dados brutos
        raw_file = scraper.save_raw_data(
            scraping_result,
            processor.raw_dir
        )
        
        # 2. PROCESSAMENTO
        logger.info("\n" + "=" * 80)
        logger.info("FASE 2: PROCESSAMENTO DE DADOS")
        logger.info("=" * 80)
        
        posts = processor.process_raw_scraping(scraping_result)
        logger.info(f"✓ {len(posts)} posts processados")
        
        # 3. ANÁLISE COM OPENAI
        logger.info("\n" + "=" * 80)
        logger.info("FASE 3: ANÁLISE COM OPENAI")
        logger.info("=" * 80)
        
        # Converter posts para dicts
        posts_data = [
            {
                "id": p.post_id,
                "url": p.url,
                "text": p.text,
                "title": p.title,
                "location": p.location,
                "price": p.price,
                "user": {"name": p.user_name},
                "topComments": [{"text": c["text"]} for c in p.comments],
                "sharedPost": {
                    "text": p.text,
                    "title": p.title,
                    "location": p.location,
                    "price": p.price,
                    "attachments": [
                        {
                            "__typename": "Photo",
                            "photo_image": {"uri": img}
                        }
                        for img in p.images
                    ]
                }
            }
            for p in posts
        ]
        
        analyses = analyzer.analyze_batch(posts_data)
        logger.info(f"✓ {len(analyses)} posts analisados")
        
        # 4. CRIAR ANÚNCIOS
        logger.info("\n" + "=" * 80)
        logger.info("FASE 4: CRIAÇÃO DE ANÚNCIOS ESTRUTURADOS")
        logger.info("=" * 80)
        
        ads = processor.create_equipment_ads(posts, analyses)
        logger.info(f"✓ {len(ads)} anúncios identificados")
        
        if len(ads) == 0:
            logger.info("Nenhum anúncio identificado. Finalizando.")
            return 0
        
        # 5. SALVAR RESULTADOS
        logger.info("\n" + "=" * 80)
        logger.info("FASE 5: SALVANDO RESULTADOS")
        logger.info("=" * 80)
        
        # Dados já foram salvos no MongoDB durante create_equipment_ads
        # Criar backup adicional em CSV/JSON
        saved_files = processor.save_backup(ads, job_type="incremental")
        
        # 6. ESTATÍSTICAS
        stats = processor.get_statistics()
        
        # Log resumo
        logger.info(f"\n📊 RESUMO:")
        logger.info(f"  Posts coletados: {total_posts}")
        logger.info(f"  Anúncios encontrados: {stats['total_ads']}")
        logger.info(f"  Taxa de conversão: {stats['total_ads']/total_posts*100:.1f}%")
        
        if stats.get('avg_price'):
            logger.info(f"  Preço médio: R$ {stats['avg_price']:.2f}")
        
        logger.info(f"\n📁 ARQUIVOS:")
        logger.info(f"  - Dados no MongoDB: ✓")
        logger.info(f"  - Backup JSON: {saved_files.get('json', 'N/A')}")
        logger.info(f"  - Backup CSV: {saved_files.get('csv', 'N/A')}")
        logger.info(f"  - Log: {log_file}")
        
        # Tempo de execução
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"\n⏱️  Tempo de execução: {duration:.1f} segundos")
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ SCRAPING INCREMENTAL CONCLUÍDO")
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ ERRO: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
