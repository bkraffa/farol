# 🗄️ Guia MongoDB - Kitesurf Scraper

## Por que MongoDB?

Para este projeto, MongoDB é ideal porque:

✅ **Dados semi-estruturados**: Posts do Facebook têm campos variáveis  
✅ **JSON nativo**: Análises da OpenAI já são JSON  
✅ **Flexível**: Fácil adicionar novos campos sem migrations  
✅ **Escalável**: Cresce facilmente de local para cloud  
✅ **Queries poderosas**: Agregações complexas e full-text search  

## 🚀 Setup Local (Desenvolvimento)

### Opção 1: Docker (Recomendado)

```bash
# Iniciar MongoDB + Mongo Express
docker-compose up -d

# Verificar se está rodando
docker ps

# Ver logs
docker-compose logs -f mongodb
```

**Acessar:**
- MongoDB: `localhost:27017`
- Mongo Express (UI): `http://localhost:8081`
  - User: `admin`
  - Password: `admin`

### Opção 2: MongoDB Local (sem Docker)

#### macOS
```bash
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```

#### Ubuntu/Debian
```bash
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
```

#### Windows
Download: https://www.mongodb.com/try/download/community

### Configurar .env

```env
# Local com Docker
MONGODB_URI=mongodb://admin:admin123@localhost:27017/

# Local sem autenticação
MONGODB_URI=mongodb://localhost:27017/
```

## ☁️ Setup Cloud (MongoDB Atlas)

### 1. Criar Conta Gratuita

1. Acesse: https://www.mongodb.com/cloud/atlas/register
2. Crie uma conta (gratuito)
3. Crie um cluster M0 (tier gratuito)

### 2. Configurar Acesso

**2.1 Database Access:**
- Vá em "Database Access"
- Crie um usuário (ex: `kitesurf_user`)
- Anote senha

**2.2 Network Access:**
- Vá em "Network Access"
- Clique "Add IP Address"
- Escolha "Allow Access from Anywhere" (0.0.0.0/0)
  - ⚠️ Produção: especifique IPs específicos

### 3. Obter Connection String

1. Vá em "Database" → "Connect"
2. Escolha "Connect your application"
3. Copie o connection string:
```
mongodb+srv://kitesurf_user:<password>@cluster0.xxxxx.mongodb.net/
```

### 4. Configurar .env

```env
# Substitua <password> pela senha real
MONGODB_URI=mongodb+srv://kitesurf_user:SUA_SENHA@cluster0.xxxxx.mongodb.net/kitesurf
```

## 📊 Estrutura do Banco

### Database: `kitesurf`

### Collections:

#### 1. **raw_posts**
Posts brutos do scraping do Apify

```javascript
{
  _id: ObjectId,
  post_id: "unique_id",
  url: "https://facebook.com/...",
  time: "2025-01-15T10:30:00Z",
  user_name: "João Silva",
  text: "Vendo Duotone...",
  title: "Duotone Rebel 12m",
  price: "R$ 4500",
  location: "Fortaleza, CE",
  group_url: "https://facebook.com/groups/...",
  group_title: "Kite Cumbuco",
  likes_count: 15,
  comments_count: 8,
  shares_count: 2,
  images: ["url1", "url2"],
  comments: [
    {text: "Aceita troca?", author: "Maria"}
  ],
  scraped_at: ISODate("2025-01-15T10:35:00Z")
}
```

#### 2. **equipment_ads**
Anúncios analisados e estruturados

```javascript
{
  _id: ObjectId,
  post_id: "unique_id",
  post_url: "https://facebook.com/...",
  is_advertisement: true,
  confidence_score: 0.95,
  equipment_type: "kite",
  brand: "Duotone",
  model: "Rebel SLS",
  year: 2024,
  size: "12m",
  condition: "seminovo",
  has_repair: false,
  price: 4500.0,
  currency: "BRL",
  city: "Fortaleza",
  state: "CE",
  description: "Kite em ótimo estado...",
  additional_items: ["bag", "válvula extra"],
  contact_info: "(85) 99999-9999",
  seller_name: "João Silva",
  analyzed_at: ISODate("2025-01-15T10:40:00Z")
}
```

### Índices

Criados automaticamente pelo sistema:

```javascript
// raw_posts
{post_id: 1}  // unique
{scraped_at: -1}
{group_url: 1}

// equipment_ads
{post_id: 1}  // unique
{analyzed_at: -1}
{is_advertisement: 1}
{equipment_type: 1}
{brand: 1}
{state: 1}
{price: 1}
// Índice composto
{is_advertisement: 1, equipment_type: 1, brand: 1}
// Full-text search
{description: "text", brand: "text", model: "text"}
```

## 🔍 Queries Úteis

### Buscar Anúncios

```python
from src.database import get_db

# Buscar kites Duotone
with get_db() as db:
    kites = db.search_ads(
        equipment_type='kite',
        brand='Duotone',
        max_price=5000
    )

# Anúncios recentes (últimas 24h)
with get_db() as db:
    recent = db.get_recent_ads(hours=24)

# Busca por texto
with get_db() as db:
    results = db.text_search('rebel sls 2024')
```

### Shell MongoDB

```bash
# Conectar
mongosh "mongodb://admin:admin123@localhost:27017/"

# Usar database
use kitesurf

# Ver collections
show collections

# Contar documentos
db.equipment_ads.countDocuments({is_advertisement: true})

# Buscar anúncios de kites
db.equipment_ads.find({
  is_advertisement: true,
  equipment_type: 'kite'
}).limit(10)

# Agregação: preço médio por marca
db.equipment_ads.aggregate([
  {$match: {is_advertisement: true, price: {$ne: null}}},
  {$group: {
    _id: '$brand',
    avg_price: {$avg: '$price'},
    count: {$sum: 1}
  }},
  {$sort: {count: -1}}
])

# Buscar anúncios baratos em Fortaleza
db.equipment_ads.find({
  is_advertisement: true,
  city: 'Fortaleza',
  price: {$lt: 3000}
})
```

## 📈 Estatísticas

### Via Python

```python
from src.database import get_db

with get_db() as db:
    stats = db.get_statistics()
    
    print(f"Total de anúncios: {stats['total_ads']}")
    print(f"Por tipo: {stats['by_equipment_type']}")
    print(f"Top marcas: {stats['top_brands']}")
    print(f"Preço médio: R$ {stats['prices']['avg']:.2f}")
```

### Via Mongo Express (UI)

1. Acesse http://localhost:8081
2. Navegue: `kitesurf` → `equipment_ads`
3. Use o query builder

## 💾 Backup e Restore

### Backup

```bash
# Backup completo
mongodump --uri="mongodb://admin:admin123@localhost:27017/" --out=backup/

# Backup de uma collection
mongodump --uri="mongodb://admin:admin123@localhost:27017/" --db=kitesurf --collection=equipment_ads --out=backup/

# Backup do Atlas (cloud)
mongodump --uri="mongodb+srv://user:pass@cluster.mongodb.net/" --out=backup/
```

### Restore

```bash
# Restore completo
mongorestore --uri="mongodb://admin:admin123@localhost:27017/" backup/

# Restore de uma collection
mongorestore --uri="mongodb://admin:admin123@localhost:27017/" --db=kitesurf --collection=equipment_ads backup/kitesurf/equipment_ads.bson
```

## 📤 Export para CSV

### Via Python

```python
from src.database import get_db

with get_db() as db:
    # Exportar todos os anúncios
    db.export_to_csv('exports/all_ads.csv')
    
    # Exportar filtrado
    db.export_to_csv(
        'exports/kites_duotone.csv',
        query={'equipment_type': 'kite', 'brand': 'Duotone'}
    )
```

### Via mongoexport

```bash
mongoexport --uri="mongodb://admin:admin123@localhost:27017/" \
  --db=kitesurf \
  --collection=equipment_ads \
  --type=csv \
  --fields=brand,model,year,price,city,state \
  --out=exports/ads.csv
```

## 🔧 Manutenção

### Limpar dados antigos

```python
from src.database import get_db
from datetime import datetime, timedelta

with get_db() as db:
    # Remover posts com mais de 1 ano
    cutoff = datetime.utcnow() - timedelta(days=365)
    result = db.db.raw_posts.delete_many({
        'scraped_at': {'$lt': cutoff}
    })
    print(f"Removidos {result.deleted_count} posts antigos")
```

### Ver tamanho do banco

```bash
mongosh "mongodb://admin:admin123@localhost:27017/"

use kitesurf
db.stats()
```

## 🚨 Troubleshooting

### Erro: "Connection refused"

```bash
# Verificar se MongoDB está rodando
docker ps  # Se usando Docker
sudo systemctl status mongod  # Linux local
brew services list  # macOS
```

### Erro: "Authentication failed"

Verifique credenciais no `.env`:
```env
MONGODB_URI=mongodb://admin:admin123@localhost:27017/
```

### MongoDB Atlas: "IP not whitelisted"

1. Vá em "Network Access" no Atlas
2. Adicione seu IP ou 0.0.0.0/0 (desenvolvimento)

### Banco muito grande

```python
# Limpar dados de teste
from src.database import get_db

with get_db() as db:
    db.db.raw_posts.delete_many({})
    db.db.equipment_ads.delete_many({})
```

## 🎯 Boas Práticas

1. **Use índices**: Já criados automaticamente pelo sistema
2. **Backup regular**: Configure backup diário/semanal
3. **Monitore tamanho**: Atlas free tier tem limite de 512 MB
4. **Segurança**: Use senhas fortes, restrinja IPs em produção
5. **Query optimization**: Use .explain() para debug

## 📚 Recursos

- [MongoDB Docs](https://docs.mongodb.com/)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- [Mongo Express](https://github.com/mongo-express/mongo-express)
- [PyMongo Docs](https://pymongo.readthedocs.io/)

## 💰 Custos MongoDB Atlas

### Free Tier (M0)
- 512 MB storage
- Shared RAM
- **Custo: $0/mês**
- Suficiente para ~50k-100k anúncios

### Paid Tiers
- M10: $0.08/hora (~$57/mês) - 10GB
- M20: $0.20/hora (~$144/mês) - 20GB
- M30: $0.54/hora (~$389/mês) - 40GB

**Recomendação**: Comece com free tier, upgrade quando necessário.
