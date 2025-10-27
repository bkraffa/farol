#!/bin/bash
# Script de agendamento para execução automática
# Adicione ao crontab para rodar 2x por dia (8h e 20h)

# Configuração
PROJECT_DIR="/path/to/kitesurf-scraper"
PYTHON="/usr/bin/python3"

# Ativar ambiente virtual se existir
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

# Executar script incremental
cd "$PROJECT_DIR"
$PYTHON scripts/run_incremental.py

# Instruções para adicionar ao crontab:
# 
# 1. Edite este arquivo e atualize PROJECT_DIR para o caminho correto
# 2. Torne o arquivo executável: chmod +x scripts/schedule_jobs.sh
# 3. Adicione ao crontab: crontab -e
# 4. Adicione as linhas:
#
# # Kitesurf Scraper - Executa às 8h e 20h todos os dias
# 0 8,20 * * * /path/to/kitesurf-scraper/scripts/schedule_jobs.sh >> /path/to/kitesurf-scraper/logs/cron.log 2>&1
#
# 5. Salve e feche
