#!/usr/bin/env python3
"""
Exemplo de uso prático do Resale Score
Encontre os melhores negócios automaticamente
"""
import sys
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_db


def find_hot_deals():
    """Encontra os melhores negócios (alto score + preço baixo)"""
    print("\n🔥 BUSCANDO HOT DEALS...\n")
    
    with get_db() as db:
        # Buscar anúncios com score ≥75 e preço razoável
        pipeline = [
            {'$match': {
                'is_advertisement': True,
                'resale_score': {'$gte': 75},
                'price': {'$lte': 6000}  # Até R$ 6k
            }},
            {'$sort': {'resale_score': -1}},
            {'$limit': 10}
        ]
        
        hot_deals = list(db.db.equipment_ads.aggregate(pipeline))
        
        if not hot_deals:
            print("❌ Nenhum hot deal encontrado no momento")
            return
        
        print(f"✅ {len(hot_deals)} hot deals encontrados!\n")
        print("=" * 80)
        
        for i, ad in enumerate(hot_deals, 1):
            score = ad.get('resale_score', 0)
            emoji = "🔥🔥🔥" if score >= 85 else "🔥🔥"
            
            print(f"\n{i}. {emoji} {ad.get('brand', 'N/A')} {ad.get('model', 'N/A')}")
            print(f"   Score: {score}/100")
            print(f"   Tipo: {ad.get('equipment_type', 'N/A')} | Tamanho: {ad.get('size', 'N/A')}")
            print(f"   Ano: {ad.get('year', 'N/A')} | Condição: {ad.get('condition', 'N/A')}")
            print(f"   💰 Preço: R$ {ad.get('price', 0):.2f}")
            print(f"   📍 {ad.get('city', 'N/A')}/{ad.get('state', 'N/A')}")
            print(f"   📝 {ad.get('resale_notes', 'N/A')}")
            print(f"   🔗 {ad.get('post_url', 'N/A')}")


def compare_deals():
    """Compara dois kites similares"""
    print("\n📊 COMPARAÇÃO DE KITES DUOTONE 12M\n")
    
    with get_db() as db:
        kites = list(db.db.equipment_ads.find({
            'brand': {'$regex': 'Duotone', '$options': 'i'},
            'size': '12m',
            'equipment_type': 'kite'
        }).sort('resale_score', -1).limit(5))
        
        if len(kites) < 2:
            print("❌ Poucos kites Duotone 12m para comparar")
            return
        
        print("=" * 80)
        for i, kite in enumerate(kites, 1):
            score = kite.get('resale_score', 0)
            price = kite.get('price', 0)
            
            print(f"\n{i}. {kite.get('model', 'N/A')} ({kite.get('year', 'N/A')})")
            print(f"   Score: {score}/100")
            print(f"   Preço: R$ {price:.2f}")
            print(f"   R$/ponto: R$ {price/score:.2f}" if score > 0 else "   R$/ponto: N/A")
            print(f"   Condição: {kite.get('condition', 'N/A')}")
            print(f"   Reparo: {'Sim' if kite.get('has_repair') else 'Não'}")
            print(f"   Local: {kite.get('city', 'N/A')}")
            print(f"   Notas: {kite.get('resale_notes', 'N/A')}")


def analyze_brand_potential():
    """Analisa potencial por marca"""
    print("\n📈 ANÁLISE DE POTENCIAL POR MARCA\n")
    
    with get_db() as db:
        pipeline = [
            {'$match': {
                'is_advertisement': True,
                'brand': {'$ne': None},
                'resale_score': {'$ne': None}
            }},
            {'$group': {
                '_id': '$brand',
                'avg_score': {'$avg': '$resale_score'},
                'avg_price': {'$avg': '$price'},
                'count': {'$sum': 1},
                'high_potential': {
                    '$sum': {'$cond': [{'$gte': ['$resale_score', 70]}, 1, 0]}
                }
            }},
            {'$sort': {'avg_score': -1}},
            {'$limit': 10}
        ]
        
        brands = list(db.db.equipment_ads.aggregate(pipeline))
        
        print("=" * 80)
        print(f"{'Marca':<20} {'Score Médio':<12} {'Preço Médio':<12} {'Alto Pot.':<10} {'Total'}")
        print("-" * 80)
        
        for brand in brands:
            name = brand['_id'][:18]
            score = brand['avg_score']
            price = brand['avg_price'] or 0
            high = brand['high_potential']
            total = brand['count']
            percentage = (high / total * 100) if total > 0 else 0
            
            print(f"{name:<20} {score:>5.1f}/100    R$ {price:>7.2f}    {high:>2}/{total:>2} ({percentage:>3.0f}%)   {total}")


def recent_opportunities():
    """Mostra oportunidades recentes"""
    print("\n⏰ OPORTUNIDADES DAS ÚLTIMAS 48H\n")
    
    from datetime import datetime, timedelta
    
    with get_db() as db:
        cutoff = datetime.utcnow() - timedelta(hours=48)
        
        recent = list(db.db.equipment_ads.find({
            'is_advertisement': True,
            'analyzed_at': {'$gte': cutoff},
            'resale_score': {'$gte': 65}
        }).sort('resale_score', -1).limit(10))
        
        if not recent:
            print("❌ Nenhuma oportunidade nas últimas 48h")
            return
        
        print(f"✅ {len(recent)} oportunidades encontradas!\n")
        print("=" * 80)
        
        for i, ad in enumerate(recent, 1):
            hours_ago = (datetime.utcnow() - ad['analyzed_at']).total_seconds() / 3600
            
            print(f"\n{i}. {ad.get('brand', 'N/A')} {ad.get('model', 'N/A')}")
            print(f"   Score: {ad.get('resale_score', 0)}/100")
            print(f"   Preço: R$ {ad.get('price', 0):.2f}")
            print(f"   ⏰ Há {hours_ago:.1f}h")
            print(f"   📍 {ad.get('city', 'N/A')}/{ad.get('state', 'N/A')}")


def main():
    """Menu de exemplos"""
    print("""
🎯 EXEMPLOS DE USO - RESALE SCORE

Escolha uma opção:
1. 🔥 Encontrar hot deals (score alto + preço bom)
2. 📊 Comparar kites similares
3. 📈 Análise por marca
4. ⏰ Oportunidades recentes (48h)
5. 🎨 Todos os exemplos
6. ❌ Sair
    """)
    
    choice = input("Opção (1-6): ").strip()
    
    try:
        if choice == '1':
            find_hot_deals()
        elif choice == '2':
            compare_deals()
        elif choice == '3':
            analyze_brand_potential()
        elif choice == '4':
            recent_opportunities()
        elif choice == '5':
            find_hot_deals()
            compare_deals()
            analyze_brand_potential()
            recent_opportunities()
        elif choice == '6':
            print("\n👋 Até logo!")
            return
        else:
            print("❌ Opção inválida")
    
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
