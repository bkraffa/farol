#!/usr/bin/env python3
"""
Script de configuração inicial do projeto
"""
import os
import sys
from pathlib import Path

def setup():
    """Configura o projeto pela primeira vez"""
    print("=" * 80)
    print("SETUP: Kitesurf Equipment Scraper")
    print("=" * 80)
    
    root_dir = Path(__file__).parent.parent
    
    # 1. Criar diretórios
    print("\n1. Criando estrutura de diretórios...")
    dirs = [
        "data/raw",
        "data/processed",
        "data/analyzed",
        "logs",
        "config"
    ]
    
    for dir_path in dirs:
        full_path = root_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {dir_path}")
    
    # 2. Verificar/criar .env
    print("\n2. Configurando variáveis de ambiente...")
    env_file = root_dir / "config" / ".env"
    env_example = root_dir / "config" / ".env.example"
    
    if not env_file.exists():
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print(f"  ✓ Arquivo .env criado de .env.example")
            print(f"  ⚠️  IMPORTANTE: Edite {env_file} com suas chaves de API")
        else:
            print(f"  ⚠️  Arquivo .env.example não encontrado")
    else:
        print(f"  ✓ Arquivo .env já existe")
    
    # 3. Verificar dependências
    print("\n3. Verificando dependências...")
    try:
        import apify_client
        print("  ✓ apify-client instalado")
    except ImportError:
        print("  ✗ apify-client NÃO instalado")
    
    try:
        import openai
        print("  ✓ openai instalado")
    except ImportError:
        print("  ✗ openai NÃO instalado")
    
    try:
        import pandas
        print("  ✓ pandas instalado")
    except ImportError:
        print("  ✗ pandas NÃO instalado")
    
    # 4. Tornar scripts executáveis
    print("\n4. Configurando permissões dos scripts...")
    scripts = [
        "scripts/run_historical.py",
        "scripts/run_incremental.py",
        "scripts/schedule_jobs.sh"
    ]
    
    for script in scripts:
        script_path = root_dir / script
        if script_path.exists():
            os.chmod(script_path, 0o755)
            print(f"  ✓ {script}")
    
    # 5. Instruções finais
    print("\n" + "=" * 80)
    print("SETUP CONCLUÍDO!")
    print("=" * 80)
    print("\nPRÓXIMOS PASSOS:")
    print("\n1. Instalar dependências:")
    print("   pip install -r requirements.txt")
    print("\n2. Configurar suas chaves de API no arquivo:")
    print(f"   {env_file}")
    print("\n3. Configurar grupos do Facebook em:")
    print(f"   {root_dir / 'config' / 'groups.json'}")
    print("\n4. Executar scraping histórico (uma vez):")
    print("   python scripts/run_historical.py")
    print("\n5. Agendar scraping incremental (2x por dia):")
    print("   Edite scripts/schedule_jobs.sh e adicione ao crontab")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    setup()
