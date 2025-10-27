# 📝 CHANGELOG

## v2.0.0 - Migração para MongoDB (2025-01-15)

### 🎉 Principais Mudanças

**Persistência com MongoDB**
- ✅ Substituição de CSV por MongoDB como banco de dados principal
- ✅ Suporte para MongoDB local (Docker) e cloud (Atlas)
- ✅ Schemas flexíveis para dados semi-estruturados
- ✅ Índices otimizados para queries rápidas
- ✅ Full-text search nativo

### 🆕 Novos Arquivos

**Backend:**
- `src/database.py` - Camada completa de persistência MongoDB
- `docker-compose.yml` - MongoDB + Mongo Express para dev local
- `scripts/query_db.py` - CLI para queries no MongoDB

**Documentação:**
- `MONGODB.md` - Guia completo do MongoDB
- `CHANGELOG.md` - Este arquivo

### 🔄 Arquivos Modificados

**Core:**
- `src/data_processor.py` - Integração com MongoDB
- `scripts/run_historical.py` - Usa MongoDB para persistência
- `scripts/run_incremental.py` - Usa MongoDB para persistência

**Configuração:**
- `requirements.txt` - Adicionado `pymongo==4.6.0`
- `config/.env.example` - Adicionado `MONGODB_URI`
- `QUICKSTART.md` - Atualizado com instruções MongoDB

### 📦 Estrutura de Dados

**Collections MongoDB:**

1. **raw_posts** - Posts brutos do Facebook
   - Índices: post_id (unique), scraped_at, group_url

2. **equipment_ads** - Anúncios estruturados
   - Índices: post_id (unique), analyzed_at, equipment_type, brand, state, price
   - Full-text search em: description, brand, model

### 🎯 Benefícios da Mudança

**Performance:**
- ⚡ Queries 10-100x mais rápidas que CSV
- 📊 Agregações complexas nativas
- 🔍 Full-text search integrado

**Funcionalidades:**
- 🔄 Updates em tempo real
- 📈 Estatísticas dinâmicas
- 🎨 Queries flexíveis com filtros múltiplos
- 🌐 Escalabilidade para cloud

**Desenvolvimento:**
- 🐳 Docker para setup instantâneo
- 🌍 MongoDB Atlas (cloud) gratuito
- 🎨 Mongo Express UI para visualização
- 🛠️ CLI de queries (`query_db.py`)

### 🔧 Migration Guide

**De CSV para MongoDB:**

Se você já tem dados em CSV, migre assim:

```python
import pandas as pd
from src.database import get_db
from src.models import EquipmentAd

# Ler CSV antigo
df = pd.read_csv('data/analyzed/old_data.csv')

# Converter para EquipmentAd objects
ads = []
for _, row in df.iterrows():
    ad = EquipmentAd(**row.to_dict())
    ads.append(ad)

# Salvar no MongoDB
with get_db() as db:
    db.save_equipment_ads(ads)
```

### 📊 Comparação de Recursos

| Recurso | v1.0 (CSV) | v2.0 (MongoDB) |
|---------|------------|----------------|
| Persistência | CSV | MongoDB |
| Queries | Pandas | Queries nativas |
| Full-text search | ❌ | ✅ |
| Índices | ❌ | ✅ |
| Agregações | Pandas | MongoDB native |
| Escalabilidade | Limitada | Ilimitada |
| Cloud-ready | ❌ | ✅ (Atlas) |
| UI visual | ❌ | ✅ (Mongo Express) |
| Backup | Manual | Automático |
| Performance (1M docs) | Lento | Rápido |

### 💾 Compatibilidade com CSV

**Backups em CSV ainda funcionam:**
- `processor.save_backup()` cria JSONs/CSVs
- `db.export_to_csv()` exporta do MongoDB
- Análise com Pandas continua possível

### 🚀 Como Atualizar

**1. Instalar novas dependências:**
```bash
pip install -r requirements.txt
```

**2. Iniciar MongoDB:**
```bash
docker-compose up -d
```

**3. Atualizar .env:**
```env
MONGODB_URI=mongodb://admin:admin123@localhost:27017/
```

**4. Rodar normalmente:**
```bash
python scripts/run_historical.py
```

### 📖 Documentação Atualizada

- **MONGODB.md** - Guia completo do MongoDB
- **QUICKSTART.md** - Atualizado com setup do MongoDB
- **ARCHITECTURE.md** - Diagrama atualizado
- **README.md** - Menção ao MongoDB

### 🐛 Breaking Changes

**Mudanças incompatíveis com v1.0:**

1. `save_analyzed_data()` → `save_backup()` + MongoDB automático
2. `generate_statistics()` → `get_statistics()` (do MongoDB)
3. Requer MongoDB rodando (local ou cloud)

**Solução temporária:**
```python
# Usar modo legacy sem MongoDB
processor = DataProcessor(use_mongodb=False)
```

### 🎯 Próximos Passos (v2.1)

Planejado para próximas versões:

- [ ] Dashboard web com análises
- [ ] API REST para consultas
- [ ] Alertas por email/Slack
- [ ] Machine learning para preços
- [ ] Suporte a PostgreSQL alternativo
- [ ] Sincronização com Google Sheets

### 🙏 Migração Assistida

Precisa de ajuda? Consulte:
- **MONGODB.md** - Setup completo
- **QUICKSTART.md** - Guia rápido
- **scripts/query_db.py** - CLI de queries

---

## v1.0.0 - Release Inicial (2025-01-14)

### ✨ Features

- Scraping automático do Facebook via Apify
- Análise inteligente com GPT-4 Vision
- Export para CSV e JSON
- Scripts de scraping histórico e incremental
- Documentação completa
- Exemplos de uso

### 📦 Arquivos

- 10 arquivos Python (~1,400 linhas)
- 7 arquivos de documentação
- Estrutura completa do projeto

---

**Versão atual: 2.0.0**  
**Data: 2025-01-15**
