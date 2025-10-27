# Kitesurf Equipment Scraper & Analyzer

Sistema automatizado para scraping de grupos do Facebook de equipamentos de kitesurfe e análise inteligente com OpenAI.

## 📋 Funcionalidades

- **Scraping Histórico**: Busca posts dos últimos 2 anos (execução única)
- **Scraping Incremental**: Busca posts das últimas 12 horas (2x por dia)
- **Análise Inteligente**: Usa GPT-4 Vision para analisar texto, imagens e comentários
- **Extração Estruturada**: Identifica anúncios e extrai dados estruturados

## 🗂️ Estrutura do Projeto

```
kitesurf-scraper/
├── config/
│   ├── groups.json           # Lista de grupos do Facebook
│   └── .env                   # Variáveis de ambiente
├── src/
│   ├── apify_scraper.py      # Cliente Apify
│   ├── openai_analyzer.py    # Análise com OpenAI
│   ├── data_processor.py     # Processamento de dados
│   └── models.py             # Schemas de dados
├── scripts/
│   ├── run_historical.py     # Script para scraping histórico
│   ├── run_incremental.py    # Script para scraping incremental
│   └── schedule_jobs.sh      # Agendamento com cron
├── data/
│   ├── raw/                  # Dados brutos do Apify
│   ├── processed/            # Dados processados
│   └── analyzed/             # Análises da OpenAI
└── logs/                     # Logs de execução
```

## 🚀 Setup

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Crie o arquivo `config/.env`:

```env
APIFY_API_TOKEN=seu_token_apify
OPENAI_API_KEY=sua_chave_openai
OPENAI_MODEL=gpt-4o-mini  # ou gpt-4o para melhor qualidade
```

### 3. Configurar grupos do Facebook

Edite `config/groups.json` com os grupos desejados.

## 📊 Uso

### Scraping Histórico (2 anos)

```bash
python scripts/run_historical.py
```

### Scraping Incremental (últimas 12 horas)

```bash
python scripts/run_incremental.py
```

### Agendar execuções automáticas

```bash
# Adicionar ao crontab
# Executa às 8h e 20h todos os dias
0 8,20 * * * /path/to/scripts/run_incremental.py
```

## 📦 Dados Extraídos

Para cada anúncio, o sistema extrai:

- ✅ **is_advertisement**: Se é realmente um anúncio
- 🏷️ **brand**: Marca do equipamento (Duotone, North, Cabrinha, etc)
- 📦 **model**: Modelo específico
- 📅 **year**: Ano do equipamento
- 💰 **price**: Preço em reais
- 📍 **city**: Cidade do anúncio
- 🗺️ **state**: Estado (sigla)
- 🔧 **has_repair**: Se tem reparos
- 🏷️ **equipment_type**: Tipo (kite, board, bar, harness, etc)
- 📏 **size**: Tamanho (para kites e pranchas)
- 🆕 **condition**: Estado (novo, usado, etc)
- 📝 **additional_items**: Itens adicionais incluídos
- 📱 **contact_info**: Informações de contato

## 🤖 Como Funciona

1. **Apify** faz scraping dos posts dos grupos
2. Sistema baixa imagens dos posts
3. **GPT-4 Vision** analisa:
   - Texto do post
   - Imagens anexadas
   - Comentários relevantes
4. Dados estruturados são salvos em JSON/CSV

## 📈 Monitoramento

Logs são salvos em `logs/` com formato:
- `historical_YYYY-MM-DD.log`
- `incremental_YYYY-MM-DD_HH-MM.log`
