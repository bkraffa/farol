#!/usr/bin/env python3
"""
Utilitário para queries no MongoDB
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_db


def print_json(data):
    """Pretty print JSON"""
    print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


def stats_command():
    """Mostra estatísticas do banco"""
    with get_db() as db:
        stats = db.get_statistics()
        
        print("\n📊 ESTATÍSTICAS DO BANCO\n")
        print(f"Posts brutos: {stats['total_raw_posts']}")
        print(f"Anúncios: {stats['total_ads']}")
        print(f"Com reparo: {stats['with_repair']}")
        
        if stats.get('prices'):
            print(f"\n💰 PREÇOS:")
            print(f"  Médio: R$ {stats['prices']['avg']:.2f}")
            print(f"  Mediana: R$ {stats['prices']['median']:.2f}")
            print(f"  Min/Max: R$ {stats['prices']['min']:.0f} - R$ {stats['prices']['max']:.0f}")
        
        print(f"\n🏷️  POR TIPO:")
        for tipo, data in stats.get('by_equipment_type', {}).items():
            print(f"  {tipo}: {data['count']} anúncios", end='')
            if data.get('avg_price'):
                print(f" (média: R$ {data['avg_price']:.2f})")
            else:
                print()
        
        print(f"\n🔝 TOP 5 MARCAS:")
        for i, item in enumerate(stats.get('top_brands', [])[:5], 1):
            print(f"  {i}. {item['brand']}: {item['count']} anúncios")
        
        print(f"\n📍 POR ESTADO:")
        for state, count in list(stats.get('by_state', {}).items())[:5]:
            print(f"  {state}: {count} anúncios")


def search_command(args):
    """Busca anúncios"""
    filters = {}
    
    # Parse argumentos
    for arg in args:
        if '=' in arg:
            key, value = arg.split('=', 1)
            
            if key == 'brand':
                filters['brand'] = value
            elif key == 'type':
                filters['equipment_type'] = value
            elif key == 'state':
                filters['state'] = value.upper()
            elif key == 'min_price':
                filters['min_price'] = float(value)
            elif key == 'max_price':
                filters['max_price'] = float(value)
            elif key == 'repair':
                filters['has_repair'] = value.lower() in ['true', '1', 'yes']
    
    with get_db() as db:
        results = db.search_ads(**filters, limit=20)
        
        print(f"\n🔍 BUSCA: {len(results)} resultados\n")
        
        for i, ad in enumerate(results, 1):
            print(f"{i}. {ad.get('brand', 'N/A')} {ad.get('model', 'N/A')} ({ad.get('year', 'N/A')})")
            print(f"   Tipo: {ad.get('equipment_type', 'N/A')} | Tamanho: {ad.get('size', 'N/A')}")
            if ad.get('price'):
                print(f"   Preço: R$ {ad['price']:.2f}")
            print(f"   Local: {ad.get('city', 'N/A')}/{ad.get('state', 'N/A')}")
            print(f"   URL: {ad.get('post_url', 'N/A')}")
            print()


def recent_command(hours=24):
    """Mostra anúncios recentes"""
    with get_db() as db:
        results = db.get_recent_ads(hours=int(hours))
        
        print(f"\n⏰ ANÚNCIOS DAS ÚLTIMAS {hours}H: {len(results)}\n")
        
        for i, ad in enumerate(results, 1):
            print(f"{i}. {ad.get('brand', 'N/A')} {ad.get('model', 'N/A')}")
            if ad.get('price'):
                print(f"   R$ {ad['price']:.2f}")
            print(f"   {ad.get('city', 'N/A')}/{ad.get('state', 'N/A')}")
            analyzed = ad.get('analyzed_at')
            if analyzed:
                print(f"   Analisado: {analyzed}")
            print()


def export_command(filename, query_str=None):
    """Exporta para CSV"""
    query = None
    if query_str:
        query = json.loads(query_str)
    
    with get_db() as db:
        db.export_to_csv(filename, query)
        print(f"✓ Exportado para: {filename}")


def text_search_command(text):
    """Busca por texto"""
    with get_db() as db:
        results = db.text_search(text, limit=20)
        
        print(f"\n🔎 BUSCA POR '{text}': {len(results)} resultados\n")
        
        for i, ad in enumerate(results, 1):
            print(f"{i}. {ad.get('brand', 'N/A')} {ad.get('model', 'N/A')}")
            print(f"   {ad.get('description', '')[:100]}...")
            if ad.get('price'):
                print(f"   R$ {ad['price']:.2f}")
            print()


def main():
    """Menu principal"""
    if len(sys.argv) < 2:
        print("""
🗄️  MongoDB Query Tool - Kitesurf Scraper

USO:
  python scripts/query_db.py <comando> [args]

COMANDOS:
  stats                     - Estatísticas gerais
  search [filters]          - Buscar anúncios
                              Ex: brand=Duotone type=kite max_price=5000
  recent [hours]            - Anúncios recentes (default: 24h)
  text "<busca>"           - Busca por texto
  export <file> [query]     - Exportar para CSV

EXEMPLOS:
  # Estatísticas
  python scripts/query_db.py stats

  # Buscar kites Duotone até R$ 5000
  python scripts/query_db.py search brand=Duotone type=kite max_price=5000

  # Anúncios das últimas 12 horas
  python scripts/query_db.py recent 12

  # Busca por texto
  python scripts/query_db.py text "rebel sls 2024"

  # Exportar tudo
  python scripts/query_db.py export ads.csv

  # Exportar filtrado
  python scripts/query_db.py export kites.csv '{"equipment_type": "kite"}'
        """)
        return 1
    
    command = sys.argv[1]
    
    try:
        if command == 'stats':
            stats_command()
        
        elif command == 'search':
            search_command(sys.argv[2:])
        
        elif command == 'recent':
            hours = sys.argv[2] if len(sys.argv) > 2 else 24
            recent_command(hours)
        
        elif command == 'text':
            if len(sys.argv) < 3:
                print("Erro: forneça texto para buscar")
                return 1
            text_search_command(sys.argv[2])
        
        elif command == 'export':
            if len(sys.argv) < 3:
                print("Erro: forneça nome do arquivo")
                return 1
            filename = sys.argv[2]
            query = sys.argv[3] if len(sys.argv) > 3 else None
            export_command(filename, query)
        
        else:
            print(f"Comando desconhecido: {command}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
