#!/usr/bin/env python3
"""
Exemplo de uso programático do sistema
"""
import os
from dotenv import load_dotenv
from src.apify_scraper import ApifyFacebookScraper
from src.openai_analyzer import OpenAIAnalyzer
from src.data_processor import DataProcessor

# Carregar configurações
load_dotenv("config/.env")

def example_basic_usage():
    """Exemplo básico de uso"""
    
    # Inicializar componentes
    scraper = ApifyFacebookScraper(os.getenv("APIFY_API_TOKEN"))
    analyzer = OpenAIAnalyzer(os.getenv("OPENAI_API_KEY"))
    processor = DataProcessor()
    
    # 1. Fazer scraping
    groups = ["https://www.facebook.com/groups/kitecumbuco"]
    result = scraper.run_incremental_scrape(groups, hours_back=12)
    
    # 2. Processar dados
    posts = processor.process_raw_scraping(result)
    
    # 3. Analisar posts
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
                "attachments": [
                    {"__typename": "Photo", "photo_image": {"uri": img}}
                    for img in p.images
                ]
            }
        }
        for p in posts
    ]
    
    analyses = analyzer.analyze_batch(posts_data)
    
    # 4. Criar anúncios
    ads = processor.create_equipment_ads(posts, analyses)
    
    # 5. Salvar e gerar estatísticas
    processor.save_analyzed_data(ads)
    stats = processor.generate_statistics(ads)
    
    print(f"Total de anúncios: {stats['total_ads']}")
    print(f"Por tipo: {stats['by_equipment_type']}")
    print(f"Por marca: {stats['by_brand']}")


def example_analyze_single_post():
    """Exemplo de análise de um único post"""
    
    analyzer = OpenAIAnalyzer(os.getenv("OPENAI_API_KEY"))
    
    # Post de exemplo
    post = {
        "id": "test_123",
        "url": "https://facebook.com/test",
        "user": {"name": "João Silva"},
        "sharedPost": {
            "text": "Vendo Duotone Rebel 12m 2023 em perfeito estado. R$ 3500",
            "title": "Duotone Rebel 12m 2023",
            "location": "Fortaleza, CE",
            "price": "R$ 3500",
            "attachments": []
        },
        "topComments": [
            {"text": "Aceita troca?"},
            {"text": "Qual o preço final?"}
        ]
    }
    
    # Analisar
    analysis = analyzer.analyze_post(post)
    
    print("Análise:")
    print(f"  É anúncio: {analysis['is_advertisement']}")
    print(f"  Confiança: {analysis['confidence_score']}")
    print(f"  Tipo: {analysis['equipment_type']}")
    print(f"  Marca: {analysis['brand']}")
    print(f"  Modelo: {analysis['model']}")
    print(f"  Preço: R$ {analysis['price']}")
    print(f"  Localização: {analysis['city']}, {analysis['state']}")


def example_filter_ads():
    """Exemplo de filtragem de anúncios"""
    import json
    
    # Carregar dados analisados
    with open("data/analyzed/incremental_latest.json", "r") as f:
        ads = json.load(f)
    
    # Filtrar por critérios
    kites = [ad for ad in ads if ad['equipment_type'] == 'kite']
    duotone = [ad for ad in ads if ad['brand'] == 'Duotone']
    cheap = [ad for ad in ads if ad['price'] and ad['price'] < 3000]
    fortaleza = [ad for ad in ads if ad['city'] == 'Fortaleza']
    
    print(f"Total de kites: {len(kites)}")
    print(f"Anúncios Duotone: {len(duotone)}")
    print(f"Até R$ 3000: {len(cheap)}")
    print(f"Em Fortaleza: {len(fortaleza)}")


if __name__ == "__main__":
    print("Escolha um exemplo:")
    print("1. Uso básico completo")
    print("2. Análise de post único")
    print("3. Filtrar anúncios")
    
    choice = input("\nOpção (1-3): ")
    
    if choice == "1":
        example_basic_usage()
    elif choice == "2":
        example_analyze_single_post()
    elif choice == "3":
        example_filter_ads()
    else:
        print("Opção inválida")
