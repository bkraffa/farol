# 🚀 Guia de Início Rápido

## Instalação em 5 minutos

### 1. Clone o repositório
```bash
git clone <seu-repo>
cd kitesurf-scraper
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Inicie o MongoDB (Local)

**Opção A: Com Docker (Recomendado)**
```bash
docker-compose up -d
```

**Opção B: MongoDB local**
```bash
# macOS
brew services start mongodb-community

# Linux
sudo systemctl start mongod
```

### 4. Configure suas chaves de API

Crie o arquivo `config/.env`:
```bash
cp config/.env.example config/.env
```

Edite `config/.env` e adicione:
```env
APIFY_API_TOKEN=seu_token_aqui
OPENAI_API_KEY=sua_chave_aqui
OPENAI_MODEL=gpt-4o-mini
```

#### Como obter as chaves:

**Apify:**
1. Acesse https://apify.com
2. Crie uma conta gratuita
3. Vá em Settings > Integrations > API tokens
4. Copie seu token

**OpenAI:**
1. Acesse https://platform.openai.com
2. Crie uma conta
3. Vá em API Keys
4. Crie uma nova chave
5. Adicione créditos (mínimo $5)

### 4. Configure os grupos

Edite `config/groups.json` e adicione os grupos do Facebook:
```json
{
  "groups": [
    {
      "url": "https://www.facebook.com/groups/SEU_GRUPO",
      "name": "Nome do Grupo",
      "active": true
    }
  ]
}
```

### 5. Execute o scraping histórico

```bash
python scripts/run_historical.py
```

Isso vai:
- Buscar posts dos últimos 2 anos
- Analisar todos com OpenAI
- Salvar resultados em `data/analyzed/`

### 6. Configure execução automática

Para rodar 2x por dia automaticamente:

```bash
# Torne o script executável
chmod +x scripts/schedule_jobs.sh

# Edite o script com o caminho correto
nano scripts/schedule_jobs.sh

# Adicione ao crontab
crontab -e

# Adicione esta linha:
0 8,20 * * * /path/to/kitesurf-scraper/scripts/schedule_jobs.sh
```

## 📊 Visualizando Resultados

### Via MongoDB UI

Acesse **Mongo Express** em http://localhost:8081
- User: `admin`
- Password: `admin`

### Via Script de Query

```bash
# Ver estatísticas
python scripts/query_db.py stats

# Buscar anúncios
python scripts/query_db.py search brand=Duotone max_price=5000

# Anúncios recentes
python scripts/query_db.py recent 24

# Exportar para CSV
python scripts/query_db.py export meus_anuncios.csv
```

### Campos no Banco

Os resultados são salvos em `data/analyzed/historical_*.json` - Dados completos
- `data/analyzed/historical_*_summary.csv` - CSV resumido (Excel)
- `data/analyzed/historical_*_stats.json` - Estatísticas

| Campo | Descrição |
|-------|-----------|
| equipment_type | Tipo (kite, board, bar, etc) |
| brand | Marca (Duotone, North, etc) |
| model | Modelo específico |
| year | Ano do equipamento |
| size | Tamanho (12m, 136x41, etc) |
| price | Preço em reais |
| condition | Estado (novo, usado, etc) |
| city | Cidade |
| state | Estado (CE, SP, RJ, etc) |
| has_repair | Tem reparo? (true/false) |
| confidence_score | Confiança da análise (0-1) |

## 💡 Dicas

### Economizar custos OpenAI

Use `gpt-4o-mini` (mais barato) em `.env`:
```env
OPENAI_MODEL=gpt-4o-mini
```

Custo aproximado:
- gpt-4o-mini: ~$0.01 por 1000 posts
- gpt-4o: ~$0.15 por 1000 posts

### Testar com poucos posts

Para testar, limite o número de posts no Apify:
```python
# Em apify_scraper.py, linha 20
"maxPosts": 10,  # Altere de 10000 para 10
```

### Monitorar execução

```bash
# Ver últimos logs
tail -f logs/incremental_*.log

# Ver estatísticas do último run
cat data/analyzed/*_stats.json | jq
```

## 🆘 Problemas Comuns

### "APIFY_API_TOKEN not found"
→ Crie o arquivo `config/.env` com suas chaves

### "No module named 'apify_client'"
→ Execute: `pip install -r requirements.txt`

### "Rate limit exceeded" (OpenAI)
→ Adicione delay entre análises ou reduza batch size

### "No posts found"
→ Verifique se os grupos estão públicos e o Apify consegue acessar

## 📞 Suporte

- Documentação completa: `README.md`
- Exemplos de código: `examples/usage_examples.py`
- Issues: (adicione link do seu repo)
