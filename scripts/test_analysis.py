#!/usr/bin/env python3
"""
Script de teste para análise OpenAI com dados já extraídos
Não faz scraping, apenas testa a análise
"""
import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.openai_analyzer import OpenAIAnalyzer
from src.data_processor import DataProcessor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_test_data(file_path):
    """Carrega dados de teste"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Se for resultado do Apify, pegar items
    if isinstance(data, dict) and 'items' in data:
        return data['items']
    # Se for lista de posts
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Formato de dados não reconhecido")


def print_analysis_result(i, post, analysis):
    """Imprime resultado da análise de forma legível"""
    print(f"\n{'=' * 80}")
    print(f"POST {i}")
    print('=' * 80)
    
    # Info do post
    post_text = post.get('sharedPost', {}).get('text') or post.get('text', '')
    print(f"\n📝 TEXTO ORIGINAL:")
    print(f"  {post_text[:200]}..." if len(post_text) > 200 else f"  {post_text}")
    
    # Resultado da análise
    print(f"\n🤖 ANÁLISE:")
    print(f"  ✓ É anúncio? {analysis.get('is_advertisement')}")
    print(f"  📊 Confiança: {analysis.get('confidence_score', 0):.2%}")
    
    if analysis.get('is_advertisement'):
        print(f"\n📦 EQUIPAMENTO:")
        print(f"  Tipo: {analysis.get('equipment_type', 'N/A')}")
        print(f"  Marca: {analysis.get('brand', 'N/A')}")
        print(f"  Modelo: {analysis.get('model', 'N/A')}")
        print(f"  Ano: {analysis.get('year', 'N/A')}")
        print(f"  Tamanho: {analysis.get('size', 'N/A')}")
        print(f"  Condição: {analysis.get('condition', 'N/A')}")
        print(f"  Tem reparo? {analysis.get('has_repair', False)}")
        
        print(f"\n💰 COMERCIAL:")
        if analysis.get('price'):
            print(f"  Preço: R$ {analysis['price']:.2f}")
        else:
            print(f"  Preço: Não informado")
        print(f"  Local: {analysis.get('city', 'N/A')}/{analysis.get('state', 'N/A')}")
        print(f"  Negociável? {analysis.get('price_negotiable', False)}")
        
        # NOVA MÉTRICA: Score de revenda
        if 'resale_score' in analysis:
            score = analysis['resale_score']
            print(f"\n🎯 POTENCIAL DE REVENDA:")
            print(f"  Score: {score.get('total_score', 0):.1f}/100")
            print(f"  Classificação: {score.get('classification', 'N/A')}")
            
            if score.get('factors'):
                print(f"\n  Fatores:")
                factors = score['factors']
                print(f"    • Marca/Modelo: {factors.get('brand_score', 0):.1f}/25")
                print(f"    • Preço: {factors.get('price_score', 0):.1f}/25")
                print(f"    • Condição: {factors.get('condition_score', 0):.1f}/25")
                print(f"    • Interesse: {factors.get('interest_score', 0):.1f}/25")
            
            if score.get('recommendation'):
                print(f"\n  💡 Recomendação: {score['recommendation']}")
        
        # Múltiplos anúncios
        if analysis.get('has_multiple_items'):
            print(f"\n📋 MÚLTIPLOS ANÚNCIOS: {analysis.get('item_count', 0)} itens")
            if analysis.get('additional_items_detailed'):
                for j, item in enumerate(analysis['additional_items_detailed'][:3], 1):
                    print(f"  Item {j}: {item}")
        
        # Extração de comentários
        extracted_from = []
        if analysis.get('extracted_from_text'):
            extracted_from.append('texto')
        if analysis.get('extracted_from_images'):
            extracted_from.append('imagens')
        if analysis.get('extracted_from_comments'):
            extracted_from.append('comentários')
        
        if extracted_from:
            print(f"\n📍 Extraído de: {', '.join(extracted_from)}")
        
        if analysis.get('analysis_notes'):
            print(f"\n📌 Notas: {analysis['analysis_notes']}")


def main():
    """Teste de análise com dados existentes"""
    print("=" * 80)
    print("TESTE DE ANÁLISE OPENAI")
    print("=" * 80)
    
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("\n❌ Uso: python scripts/test_analysis.py <arquivo_de_dados.json>")
        print("\nExemplos:")
        print("  python scripts/test_analysis.py data/tests/test_scraping_10posts.json")
        print("  python scripts/test_analysis.py /path/to/dataset_facebook.json")
        return 1
    
    data_file = Path(sys.argv[1])
    
    if not data_file.exists():
        print(f"\n❌ Arquivo não encontrado: {data_file}")
        return 1
    
    # Carregar variáveis de ambiente
    env_path = root_dir / "config" / ".env"
    load_dotenv(env_path)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    if not openai_key:
        print("\n❌ OPENAI_API_KEY não encontrado no .env")
        return 1
    
    # Carregar dados
    print(f"\n📂 Carregando dados de: {data_file}")
    try:
        posts = load_test_data(data_file)
        print(f"✓ {len(posts)} posts carregados")
    except Exception as e:
        print(f"❌ Erro ao carregar dados: {str(e)}")
        return 1
    
    # Perguntar quantos analisar
    max_analyze = min(len(posts), 10)
    num_analyze = input(f"\n🔍 Quantos posts analisar? (1-{max_analyze}, padrão: 3): ")
    num_analyze = int(num_analyze) if num_analyze else 3
    num_analyze = min(num_analyze, max_analyze)
    
    # Confirmar
    print(f"\n⚙️  Modelo: {openai_model}")
    confirm = input(f"🚀 Analisar {num_analyze} posts? (s/N): ")
    if confirm.lower() != 's':
        print("Cancelado.")
        return 0
    
    # Inicializar analisador
    analyzer = OpenAIAnalyzer(openai_key, openai_model)
    
    # Analisar posts
    print(f"\n{'=' * 80}")
    print("INICIANDO ANÁLISE")
    print('=' * 80)
    
    results = []
    stats = {
        'total': num_analyze,
        'ads': 0,
        'non_ads': 0,
        'errors': 0,
        'with_multiple_items': 0,
        'avg_confidence': 0.0,
        'avg_resale_score': 0.0
    }
    
    for i, post in enumerate(posts[:num_analyze], 1):
        print(f"\n[{i}/{num_analyze}] Analisando...")
        
        try:
            analysis = analyzer.analyze_post(post, download_images=True)
            results.append({
                'post': post,
                'analysis': analysis
            })
            
            # Estatísticas
            if analysis.get('is_advertisement'):
                stats['ads'] += 1
            else:
                stats['non_ads'] += 1
            
            if analysis.get('has_multiple_items'):
                stats['with_multiple_items'] += 1
            
            stats['avg_confidence'] += analysis.get('confidence_score', 0)
            
            if analysis.get('resale_score', {}).get('total_score'):
                stats['avg_resale_score'] += analysis['resale_score']['total_score']
            
            # Mostrar resultado
            print_analysis_result(i, post, analysis)
            
        except Exception as e:
            logger.error(f"Erro ao analisar post {i}: {str(e)}")
            stats['errors'] += 1
    
    # Estatísticas finais
    print(f"\n{'=' * 80}")
    print("ESTATÍSTICAS")
    print('=' * 80)
    print(f"\nTotal analisado: {stats['total']}")
    print(f"  ✓ Anúncios: {stats['ads']}")
    print(f"  ✗ Não anúncios: {stats['non_ads']}")
    print(f"  ⚠️  Erros: {stats['errors']}")
    
    if stats['with_multiple_items'] > 0:
        print(f"\n📋 Posts com múltiplos itens: {stats['with_multiple_items']}")
    
    if stats['total'] > 0:
        avg_conf = stats['avg_confidence'] / stats['total']
        print(f"\n📊 Confiança média: {avg_conf:.2%}")
        
        if stats['ads'] > 0 and stats['avg_resale_score'] > 0:
            avg_resale = stats['avg_resale_score'] / stats['ads']
            print(f"🎯 Score médio de revenda: {avg_resale:.1f}/100")
    
    # Salvar resultados
    output_dir = root_dir / "data" / "tests"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"test_analysis_results_{num_analyze}posts.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'stats': stats,
            'results': results
        }, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n✓ Resultados salvos em: {output_file}")
    
    # Custo estimado
    cost_per_analysis = 0.01 if 'mini' in openai_model else 0.05
    total_cost = num_analyze * cost_per_analysis
    print(f"\n💰 Custo estimado: ~${total_cost:.2f} USD")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
