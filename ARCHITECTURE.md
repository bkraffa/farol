# 🏗️ Arquitetura do Sistema

## Visão Geral

O sistema é composto por 3 camadas principais:

```
┌─────────────────────────────────────────────────────────────┐
│                     INTERFACE (Scripts)                      │
│  run_historical.py  │  run_incremental.py  │  setup.py      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                    LÓGICA DE NEGÓCIO (src/)                  │
│                                                               │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ ApifyFacebookS. │  │ OpenAIAnalyzer   │  │ DataProc.  │ │
│  │                 │  │                  │  │            │ │
│  │ - Scraping      │  │ - Análise GPT-4  │  │ - ETL      │ │
│  │ - Histórico     │  │ - Vision         │  │ - Stats    │ │
│  │ - Incremental   │  │ - Estruturação   │  │ - Export   │ │
│  └─────────────────┘  └──────────────────┘  └────────────┘ │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Models (Data Schemas)                    │   │
│  │  FacebookPost │ EquipmentAd │ EquipmentType │ etc    │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                    INTEGAÇÕES EXTERNAS                       │
│                                                               │
│  ┌──────────────┐        ┌──────────────┐                   │
│  │   Apify API  │        │  OpenAI API  │                   │
│  │              │        │              │                   │
│  │ - Scraping   │        │ - GPT-4o     │                   │
│  │ - Facebook   │        │ - Vision     │                   │
│  └──────────────┘        └──────────────┘                   │
└───────────────────────────────────────────────────────────┘
```

## Fluxo de Dados

### 1. Scraping (Apify)

```
Facebook Groups
      ↓
  Apify Actor
      ↓
Raw JSON Data
      ↓
  data/raw/
```

**Responsável:** `ApifyFacebookScraper`

**Saída:** JSON com posts, imagens, comentários, metadados

### 2. Processamento

```
Raw JSON
      ↓
Parse & Clean
      ↓
FacebookPost Objects
      ↓
  data/processed/
```

**Responsável:** `DataProcessor.process_raw_scraping()`

**Transformações:**
- Extração de texto e imagens
- Normalização de dados
- Agregação de comentários

### 3. Análise (OpenAI)

```
FacebookPost
      ↓
Prepare Prompt
      ↓
GPT-4 Vision API
      ↓
Structured JSON
      ↓
EquipmentAd Object
```

**Responsável:** `OpenAIAnalyzer`

**Inputs:**
- Texto do post
- Título
- Comentários
- Imagens (URLs)
- Localização

**Output:** JSON estruturado com:
- Classificação (é anúncio?)
- Equipamento (tipo, marca, modelo)
- Preço e localização
- Condições e reparos
- Confiança da análise

### 4. Persistência

```
EquipmentAd Objects
      ↓
  Filtering
      ↓
Export (JSON/CSV)
      ↓
  data/analyzed/
```

**Responsável:** `DataProcessor.save_analyzed_data()`

**Formatos:**
- JSON completo
- CSV completo
- CSV resumido
- Estatísticas JSON

## Componentes Principais

### 1. ApifyFacebookScraper

**Responsabilidades:**
- Configurar e executar o Apify actor
- Diferenciar scraping histórico vs incremental
- Salvar dados brutos
- Gerenciar rate limits

**Configurações:**
```python
# Histórico (2 anos)
{
    "onlyPostsNewerThan": "730 days",
    "maxPosts": 10000
}

# Incremental (12 horas)
{
    "onlyPostsNewerThan": "12 hours",
    "maxPosts": 500
}
```

### 2. OpenAIAnalyzer

**Responsabilidades:**
- Criar prompts otimizados
- Fazer chamadas para GPT-4 Vision
- Parsear respostas JSON
- Análise em batch com controle de concorrência

**Características:**
- Suporte a análise de imagens
- Sistema de fallback (texto apenas se imagens falham)
- Validação de JSON estruturado
- Logging detalhado

**Prompt Engineering:**
- System prompt com contexto de domínio
- Few-shot examples implícitos
- Estrutura JSON enforçada via response_format
- Temperature baixa (0.1) para consistência

### 3. DataProcessor

**Responsabilidades:**
- ETL (Extract, Transform, Load)
- Conversão entre formatos
- Geração de estatísticas
- Export multi-formato

**Pipeline:**
```
Raw Data → Parse → Transform → Validate → Export
```

## Modelos de Dados

### FacebookPost

```python
@dataclass
class FacebookPost:
    post_id: str
    url: str
    time: str
    user_name: str
    text: str
    title: Optional[str]
    price: Optional[str]
    location: Optional[str]
    group_url: str
    group_title: str
    likes_count: int
    comments_count: int
    shares_count: int
    images: List[str]
    comments: List[Dict]
```

### EquipmentAd

```python
@dataclass
class EquipmentAd:
    # Identificação
    post_id: str
    post_url: str
    
    # Classificação
    is_advertisement: bool
    confidence_score: float
    
    # Equipamento
    equipment_type: str
    brand: Optional[str]
    model: Optional[str]
    year: Optional[int]
    size: Optional[str]
    condition: str
    has_repair: bool
    
    # Comercial
    price: Optional[float]
    city: Optional[str]
    state: Optional[str]
    
    # Metadados
    extracted_from_text: bool
    extracted_from_images: bool
    extracted_from_comments: bool
```

## Padrões de Projeto

### 1. Strategy Pattern

Diferentes estratégias de scraping:
- `run_historical_scrape()`
- `run_incremental_scrape()`

### 2. Factory Pattern

Criação de objetos a partir de análises:
```python
EquipmentAd.from_analysis(post, analysis)
```

### 3. Pipeline Pattern

Processamento em etapas:
```
Scrape → Process → Analyze → Export
```

## Escalabilidade

### Horizontal

- Batch processing com controle de concorrência
- Stateless (pode rodar múltiplas instâncias)
- Independência entre jobs

### Vertical

- Análise incremental reduz carga
- Cache de análises (via filesystem)
- Lazy loading de imagens

## Monitoramento

### Logs

Estruturados por:
- Timestamp
- Nível (INFO, ERROR, etc)
- Componente
- Métricas

### Métricas

- Posts coletados
- Anúncios identificados
- Taxa de conversão
- Tempo de execução
- Custos API

## Custos

### OpenAI

- **gpt-4o-mini**: ~$0.01 por 1000 posts
- **gpt-4o**: ~$0.15 por 1000 posts

### Apify

- Free tier: 5GB storage, 5 horas compute/mês
- Paid: $49/mês para uso intenso

## Segurança

- Chaves API em `.env` (não commitadas)
- Validação de inputs
- Rate limiting
- Error handling robusto

## Manutenção

### Logs

```bash
logs/
├── historical_YYYYMMDD.log
└── incremental_YYYYMMDD_HHMM.log
```

### Backup

Dados em `data/` devem ter backup:
- `data/analyzed/` → Resultados finais
- `data/raw/` → Pode ser recriado via re-scraping

### Updates

- Apify actor pode mudar → Testar periodicamente
- OpenAI API evolui → Atualizar quando necessário
- Facebook muda estrutura → Adaptar parsers
