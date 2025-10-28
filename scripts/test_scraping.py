#!/usr/bin/env python3
"""
Script de teste para scraping rápido (poucos posts)
Útil para testar configuração sem gastar créditos
"""
import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.apify_scraper import ApifyFacebookScraper, load_groups_config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Teste rápido de scraping"""
    print("=" * 80)
    print("TESTE RÁPIDO DE SCRAPING")
    print("=" * 80)
    
    # Carregar variáveis de ambiente
    env_path = root_dir / "config" / ".env"
    load_dotenv(env_path)
    
    apify_token = os.getenv("APIFY_API_TOKEN")
    if not apify_token:
        logger.error("APIFY_API_TOKEN não encontrado no .env")
        return 1
    
    # Configurações
    MAX_POSTS = int(input("\n📊 Quantos posts buscar? (recomendado: 5-20): ") or "10")
    HOURS_BACK = int(input("⏰ Quantas horas para trás? (padrão: 24): ") or "24")
    
    # Carregar grupos
    config_path = root_dir / "config" / "groups.json"
    group_urls = load_groups_config(str(config_path))
    
    print(f"\n✓ Grupos configurados: {len(group_urls)}")
    for i, url in enumerate(group_urls, 1):
        print(f"  {i}. {url}")
    
    # Confirmar
    confirm = input(f"\n🚀 Buscar {MAX_POSTS} posts dos últimos {HOURS_BACK}h? (s/N): ")
    if confirm.lower() != 's':
        print("Cancelado.")
        return 0
    
    # Inicializar scraper
    scraper = ApifyFacebookScraper(apify_token)
    
    try:
        # Executar scraping
        logger.info(f"Iniciando scraping de {MAX_POSTS} posts...")
        
        run_input = {
            "startUrls": [{"url": url} for url in group_urls],
            "viewOption": "CHRONOLOGICAL",
            "onlyPostsNewerThan": f"{HOURS_BACK} hours",
            "maxPosts": MAX_POSTS,
            "resultsLimit": MAX_POSTS
        }
        
        result = scraper._run_scraper(run_input, "test")
        
        # Resultados
        items = result.get("items", [])
        print("\n" + "=" * 80)
        print(f"✓ SCRAPING CONCLUÍDO: {len(items)} posts coletados")
        print("=" * 80)
        
        if not items:
            print("\n⚠️  Nenhum post encontrado. Tente:")
            print("  - Aumentar o período (hours_back)")
            print("  - Verificar se os grupos têm posts recentes")
            print("  - Verificar se as URLs estão corretas")
            return 0
        
        # Mostrar primeiros posts
        print(f"\n📝 PRIMEIROS {min(3, len(items))} POSTS:\n")
        
        for i, item in enumerate(items[:3], 1):
            # Pegar dados do post
            if "sharedPost" in item and item["sharedPost"]:
                shared = item["sharedPost"]
                text = shared.get("text", "")
                title = shared.get("title", "")
                price = shared.get("price", "")
                location = shared.get("location", "")
            else:
                text = item.get("text", "")
                title = item.get("title", "")
                price = item.get("price", "")
                location = item.get("location", "")
            
            print(f"POST {i}:")
            print(f"  Título: {title or '(sem título)'}")
            print(f"  Texto: {text[:100]}..." if len(text) > 100 else f"  Texto: {text}")
            print(f"  Preço: {price or '(não informado)'}")
            print(f"  Local: {location or '(não informado)'}")
            print(f"  Likes: {item.get('likesCount', 0)}")
            print(f"  Comentários: {item.get('commentsCount', 0)}")
            print(f"  URL: {item.get('url', 'N/A')}")
            print()
        
        # Salvar resultado
        output_dir = root_dir / "data" / "tests"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"test_scraping_{MAX_POSTS}posts.json"
        # Handler para serializar datetime
        def json_serial(obj):
            """JSON serializer para objetos não serializáveis"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=json_serial)
        
        print(f"✓ Dados salvos em: {output_file}")
        print(f"\n💡 Para testar análise desses dados, execute:")
        print(f"   python scripts/test_analysis.py {output_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Erro no scraping: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
