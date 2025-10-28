# 🎯 Sistema de Score de Potencial de Revenda

## Visão Geral

O **Resale Score** (0-100) identifica automaticamente quais equipamentos têm maior potencial de revenda, considerando marca, ano, tamanho, preço, condição e demanda de mercado.

### Por que isso importa?

❌ **Sem o Score:**
- "Kite Duotone 2024 por R$ 4.000" → Bom ou ruim?
- "North 2019 por R$ 2.500" → Vale a pena?

✅ **Com o Score:**
- "Duotone Rebel SLS 12m 2024 - R$ 4.000" → **Score: 85/100** 🔥
  - "Marca premium, ano recente, tamanho popular, preço competitivo"
- "North Carve 9m 2019 - R$ 2.500" → **Score: 55/100** 👍
  - "Marca boa, mas modelo antigo, preço ok"

## 📊 Sistema de Pontuação

### Total: 100 pontos

#### 1. MARCA (30 pontos)
```
Top Tier (30 pts):     Duotone, North Kiteboarding
Mid Tier (20 pts):     Cabrinha, Core, Slingshot, Ozone
Entry Tier (10 pts):   Outras marcas conhecidas
Desconhecida (0 pts):  Marcas não reconhecidas
```

**Por quê?**
- Marcas premium mantêm valor
- Melhor revenda e liquidez
- Maior demanda no mercado usado

#### 2. ANO/MODELO (25 pontos)
```
2024-2025 (25 pts):  Ano atual ou anterior
2022-2023 (20 pts):  2-3 anos
2020-2021 (10 pts):  4-5 anos
Mais antigo (5 pts): Equipamento antigo
```

**Por quê?**
- Tecnologia atual = maior demanda
- Depreciação mais lenta nos primeiros anos
- Garantia pode estar válida

#### 3. TAMANHO (15 pontos) - Para Kites
```
9m-12m (15 pts):     Tamanhos populares (maioria dos riders)
7m, 14m (10 pts):    Menos comuns
<7m, >16m (5 pts):   Tamanhos raros/especializados
```

**Por quê?**
- 9-12m: 80% dos kitesurfistas usam
- Maior mercado = venda mais fácil
- Tamanhos extremos são nicho

#### 4. PREÇO vs MERCADO (20 pontos)
```
Abaixo do mercado (20 pts):  Ótimo negócio
Preço justo (15 pts):        Preço de mercado
Preço alto (5 pts):          Acima da média
Sem preço (10 pts):          Neutro
```

**Como é calculado?**
- GPT-4 compara com conhecimento do mercado
- Considera marca, ano, condição
- Exemplo: Rebel SLS 12m 2024 novo ≈ R$ 8.000, usado R$ 5-6.000

#### 5. CONDIÇÃO (10 pontos)
```
Novo/Seminovo (10 pts):       Sem reparos
Bom estado (7 pts):           Usado normal
Reparos pequenos (5 pts):     Consertos menores
Reparos grandes (2 pts):      Damage significativo
```

**Por quê?**
- Reparos reduzem valor de revenda
- Compradores preferem sem reparo
- Custo extra para reparar

## 🎨 Categorias de Score

### 🔥 Alto Potencial (70-100)
**Características:**
- Marca premium (Duotone, North)
- Ano recente (2022+)
- Tamanho popular
- Preço competitivo
- Ótima condição

**Exemplo:**
```json
{
  "brand": "Duotone",
  "model": "Rebel SLS",
  "year": 2024,
  "size": "12m",
  "price": 5500,
  "condition": "seminovo",
  "has_repair": false,
  "resale_score": 88,
  "resale_notes": "Marca premium, ano atual, tamanho popular, preço 30% abaixo do novo"
}
```

### 👍 Médio Potencial (50-69)
**Características:**
- Marca mid-tier ou premium antiga
- 3-5 anos
- Tamanho ok
- Preço justo
- Condição aceitável

**Exemplo:**
```json
{
  "brand": "Cabrinha",
  "model": "Switchblade",
  "year": 2021,
  "size": "10m",
  "price": 3200,
  "condition": "usado",
  "has_repair": false,
  "resale_score": 58,
  "resale_notes": "Marca boa, modelo um pouco antigo, preço justo"
}
```

### ⚠️ Baixo Potencial (<50)
**Características:**
- Marca entry-level ou desconhecida
- Equipamento antigo (>5 anos)
- Tamanho raro
- Preço alto ou com muitos reparos

**Exemplo:**
```json
{
  "brand": "Marca Genérica",
  "model": "Model X",
  "year": 2017,
  "size": "16m",
  "price": 4000,
  "condition": "precisa_reparo",
  "has_repair": true,
  "resale_score": 28,
  "resale_notes": "Marca desconhecida, antigo, tamanho raro, precisa reparo"
}
```

## 🔍 Como Usar

### 1. Via MongoDB Query

```python
from src.database import get_db

# Buscar alto potencial
with get_db() as db:
    hot_deals = db.get_high_potential_ads(min_score=75)
    
    for ad in hot_deals:
        print(f"{ad['brand']} {ad['model']} - Score: {ad['resale_score']}/100")
        print(f"R$ {ad['price']} - {ad['resale_notes']}")
```

### 2. Via CLI

```bash
# Alto potencial geral (≥70)
python scripts/query_db.py potential 70

# Kites com score ≥80
python scripts/query_db.py potential 80 type=kite

# Ver estatísticas
python scripts/query_db.py stats
```

### 3. Dashboard (futuro)

```
🔥 HOT DEALS
Score ≥ 80

1. Duotone Rebel SLS 12m 2024 - 88/100
   R$ 5.500 - Fortaleza/CE
   "Marca premium, ano atual, preço excelente"

2. North Carve 10m 2023 - 82/100
   R$ 3.800 - São Paulo/SP
   "Marca top, ano recente, tamanho popular"
```

## 📈 Casos de Uso

### 1. Compra para Revenda
```bash
# Buscar oportunidades
python scripts/query_db.py potential 75

# Filtrar por localização
python scripts/query_db.py search state=CE min_score=70
```

### 2. Análise de Mercado
```python
from src.database import get_db

with get_db() as db:
    stats = db.get_statistics()
    
    print(f"Score médio: {stats['resale_potential']['avg_score']}")
    print(f"Alto potencial: {stats['resale_potential']['high_potential']}")
```

### 3. Alertas Automáticos
```python
from src.database import get_db
from datetime import datetime, timedelta

# Verificar novos high-potential
cutoff = datetime.utcnow() - timedelta(hours=12)

with get_db() as db:
    new_hot = db.db.equipment_ads.find({
        'analyzed_at': {'$gte': cutoff},
        'resale_score': {'$gte': 80}
    })
    
    for ad in new_hot:
        send_alert(f"🔥 Hot deal: {ad['brand']} {ad['model']}")
```

## 🎓 Entendendo o Score

### Exemplos Práticos

#### Exemplo 1: Score Perfeito (95/100)
```
Duotone Rebel SLS 12m 2025
R$ 6.000 (novo: R$ 9.000)
Seminovo, sem reparos

Breakdown:
- Marca: 30/30 (Duotone = top tier)
- Ano: 25/25 (2025 = atual)
- Tamanho: 15/15 (12m = popular)
- Preço: 20/20 (33% abaixo do novo)
- Condição: 10/10 (seminovo, sem reparo)

Score: 100/100
Notas: "Marca premium, ano atual, tamanho popular, preço excelente"
```

#### Exemplo 2: Score Alto (78/100)
```
North Carve 10m 2023
R$ 3.500
Bom estado, sem reparos

Breakdown:
- Marca: 30/30 (North = top tier)
- Ano: 20/25 (2023 = 2 anos)
- Tamanho: 15/15 (10m = popular)
- Preço: 15/20 (preço justo)
- Condição: 7/10 (usado, mas ok)

Score: 87/100
Notas: "Marca premium, recente, preço justo"
```

#### Exemplo 3: Score Médio (52/100)
```
Cabrinha Switchblade 14m 2020
R$ 2.800
Usado, reparo pequeno

Breakdown:
- Marca: 20/30 (Cabrinha = mid tier)
- Ano: 10/25 (2020 = 5 anos)
- Tamanho: 10/15 (14m = menos comum)
- Preço: 15/20 (ok para o ano)
- Condição: 5/10 (tem reparo)

Score: 60/100
Notas: "Marca boa, mas antigo, tem reparo"
```

## 📊 Estatísticas do Sistema

### Distribuição Típica

```
Alto (≥70):    ~20-25% dos anúncios
Médio (50-69): ~50-60% dos anúncios
Baixo (<50):   ~20-25% dos anúncios
```

### Por Tipo de Equipamento

**Kites:**
- Score médio: 62/100
- Alto potencial: 23%

**Boards:**
- Score médio: 58/100
- Alto potencial: 18%

**Bars:**
- Score médio: 55/100
- Alto potencial: 15%

## 🔧 Ajustes e Customização

O sistema pode ser ajustado editando o prompt em `src/openai_analyzer.py`:

```python
# Aumentar peso do ano
"Ano/Modelo (0-35 pontos)" em vez de 25

# Adicionar novo critério
"Localização (0-10 pontos):
 - Regiões com vento forte: 10 pts
 - Outras regiões: 5 pts"
```

## 💡 Dicas

1. **Combine com outros filtros:**
   ```bash
   python scripts/query_db.py search state=CE max_price=4000 min_score=70
   ```

2. **Monitore novos high-potential:**
   ```bash
   python scripts/query_db.py recent 12 | grep "Score: [7-9]"
   ```

3. **Exporte para análise:**
   ```bash
   python scripts/query_db.py export hot_deals.csv '{"resale_score": {"$gte": 75}}'
   ```

## 📈 Roadmap

### v2.1 (Futuro)
- [ ] Machine learning para refinar scores
- [ ] Histórico de preços
- [ ] Predição de tempo de venda
- [ ] Score por região
- [ ] Comparação com vendas passadas

### v2.2
- [ ] Dashboard web com gráficos
- [ ] Alertas automáticos
- [ ] API REST para scores
- [ ] Integração com WhatsApp

---

**O Score de Revenda transforma dados brutos em insights acionáveis! 🎯**
