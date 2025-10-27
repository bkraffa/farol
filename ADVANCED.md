# ⚡ Otimizações e Dicas Avançadas

## 🎯 Reduzir Custos OpenAI

### 1. Usar modelo mais barato

```python
# Em .env
OPENAI_MODEL=gpt-4o-mini  # ~15x mais barato que gpt-4o
```

**Comparação de custos (por 1000 posts):**
- `gpt-4o-mini`: ~$0.01
- `gpt-4o`: ~$0.15

### 2. Análise sem imagens

Se o texto for suficiente:

```python
# Em openai_analyzer.py
analysis = analyzer.analyze_post(post, download_images=False)
```

Economia: ~50% de tokens

### 3. Pré-filtrar posts

Antes de enviar para OpenAI, filtre posts óbvios:

```python
def is_likely_ad(post):
    """Filtro rápido antes da análise"""
    text = post.get('text', '').lower()
    title = post.get('title', '').lower()
    
    # Palavras-chave de venda
    sell_keywords = ['vendo', 'venda', 'selling', 'sell', 'r$', 'reais']
    
    # Tem palavra-chave de venda?
    has_keyword = any(kw in text or kw in title for kw in sell_keywords)
    
    # Tem preço mencionado?
    has_price = bool(post.get('price')) or 'r$' in text
    
    return has_keyword or has_price

# Filtrar antes de analisar
posts_to_analyze = [p for p in posts if is_likely_ad(p)]
```

### 4. Rate limiting manual

```python
import time

for i, post in enumerate(posts):
    analysis = analyzer.analyze_post(post)
    
    # Pequeno delay a cada 50 posts
    if i % 50 == 0:
        time.sleep(2)
```

## 🚀 Melhorar Performance

### 1. Análise paralela

```python
from concurrent.futures import ThreadPoolExecutor

def analyze_batch_parallel(posts, max_workers=5):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(analyzer.analyze_post, p) for p in posts]
        results = [f.result() for f in futures]
    return results
```

⚠️ **Cuidado:** Respeite rate limits da OpenAI

### 2. Cache de análises

```python
import hashlib
import json
import os

class CachedAnalyzer:
    def __init__(self, analyzer, cache_dir="cache"):
        self.analyzer = analyzer
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, post):
        """Gera chave única para o post"""
        text = post.get('text', '') + post.get('title', '')
        return hashlib.md5(text.encode()).hexdigest()
    
    def analyze_post(self, post):
        cache_key = self._get_cache_key(post)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        # Verifica cache
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        # Analisa e salva no cache
        result = self.analyzer.analyze_post(post)
        with open(cache_file, 'w') as f:
            json.dump(result, f)
        
        return result
```

### 3. Processar em chunks

Para datasets grandes:

```python
def process_in_chunks(posts, chunk_size=100):
    """Processa posts em chunks menores"""
    for i in range(0, len(posts), chunk_size):
        chunk = posts[i:i+chunk_size]
        
        # Processar chunk
        analyses = analyzer.analyze_batch(chunk)
        
        # Salvar chunk intermediário
        chunk_file = f"data/temp/chunk_{i//chunk_size}.json"
        save_chunk(analyses, chunk_file)
        
        logger.info(f"Chunk {i//chunk_size} processado")
```

## 🎨 Melhorar Qualidade da Análise

### 1. Prompt Engineering

Adicione exemplos específicos ao prompt:

```python
SYSTEM_PROMPT = """...
EXEMPLOS DE ANÚNCIOS:

BOM:
"Vendo Duotone Rebel 12m 2023, sem reparos. R$ 4500. Fortaleza/CE"
→ brand: Duotone, model: Rebel, size: 12m, year: 2023, price: 4500

BOM:
"Kite North Carve 10m usado. Aceito 2800. WhatsApp (85) 9999-9999"
→ brand: North, model: Carve, size: 10m, price: 2800, contact_info: (85) 9999-9999

RUIM (não é anúncio):
"Alguém tem indicação de kite para iniciante?"
→ is_advertisement: false
"""
```

### 2. Validação pós-análise

```python
def validate_analysis(analysis):
    """Valida e corrige análises"""
    
    # Se diz que é anúncio mas não tem preço nem marca
    if analysis['is_advertisement']:
        if not analysis['price'] and not analysis['brand']:
            analysis['confidence_score'] *= 0.5  # Reduz confiança
    
    # Normalizar marcas conhecidas
    brand_aliases = {
        'duotone': ['duotone', 'dt', 'd.tone'],
        'north': ['north', 'north kiteboarding', 'nkb'],
        'cabrinha': ['cabrinha', 'cab']
    }
    
    if analysis['brand']:
        for official, aliases in brand_aliases.items():
            if analysis['brand'].lower() in aliases:
                analysis['brand'] = official.title()
    
    return analysis
```

### 3. Confidence threshold

Filtre análises de baixa confiança:

```python
high_confidence_ads = [
    ad for ad in ads 
    if ad.confidence_score >= 0.7
]
```

## 📊 Análises Avançadas

### 1. Detectar tendências de preço

```python
import pandas as pd
import matplotlib.pyplot as plt

def price_trends(ads):
    df = pd.DataFrame([ad.to_dict() for ad in ads])
    
    # Por marca
    avg_by_brand = df.groupby('brand')['price'].mean()
    
    # Por ano
    avg_by_year = df.groupby('year')['price'].mean()
    
    # Por estado
    avg_by_state = df.groupby('state')['price'].mean()
    
    return {
        'by_brand': avg_by_brand.to_dict(),
        'by_year': avg_by_year.to_dict(),
        'by_state': avg_by_state.to_dict()
    }
```

### 2. Alertas de boas ofertas

```python
def find_good_deals(ads, threshold=0.8):
    """Encontra anúncios com preço abaixo da média"""
    df = pd.DataFrame([ad.to_dict() for ad in ads])
    
    good_deals = []
    
    for brand in df['brand'].unique():
        brand_df = df[df['brand'] == brand]
        avg_price = brand_df['price'].mean()
        
        # Preços 20% abaixo da média
        cheap = brand_df[brand_df['price'] < avg_price * threshold]
        good_deals.extend(cheap.to_dict('records'))
    
    return good_deals
```

### 3. Relatório automático

```python
def generate_report(ads):
    """Gera relatório HTML com insights"""
    stats = generate_statistics(ads)
    
    html = f"""
    <html>
    <head><title>Relatório Kitesurf</title></head>
    <body>
        <h1>Relatório de Anúncios</h1>
        <h2>Resumo</h2>
        <ul>
            <li>Total de anúncios: {stats['total_ads']}</li>
            <li>Preço médio: R$ {stats['avg_price']:.2f}</li>
            <li>Equipamentos com reparo: {stats['with_repair']}</li>
        </ul>
        
        <h2>Top 5 Marcas</h2>
        <ul>
    """
    
    for brand, count in list(stats['by_brand'].items())[:5]:
        html += f"<li>{brand}: {count} anúncios</li>"
    
    html += "</ul></body></html>"
    
    with open('data/analyzed/report.html', 'w') as f:
        f.write(html)
```

## 🔔 Notificações

### 1. Email de novos anúncios

```python
import smtplib
from email.mime.text import MIMEText

def send_notification(new_ads):
    """Envia email com novos anúncios"""
    if not new_ads:
        return
    
    # Filtrar apenas os interessantes
    interesting = [
        ad for ad in new_ads 
        if ad.price and ad.price < 5000
    ]
    
    if not interesting:
        return
    
    # Criar mensagem
    body = "Novos anúncios interessantes:\n\n"
    for ad in interesting[:10]:
        body += f"- {ad.brand} {ad.model} ({ad.size}): R$ {ad.price}\n"
        body += f"  {ad.city}/{ad.state} - {ad.post_url}\n\n"
    
    msg = MIMEText(body)
    msg['Subject'] = f'{len(interesting)} novos anúncios de kitesurf'
    msg['From'] = 'bot@example.com'
    msg['To'] = 'seu@email.com'
    
    # Enviar (configure SMTP)
    # server = smtplib.SMTP('smtp.gmail.com', 587)
    # server.send_message(msg)
```

### 2. Webhook para Slack/Discord

```python
import requests

def notify_slack(ads):
    """Envia notificação para Slack"""
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    
    message = {
        "text": f"🏄 {len(ads)} novos anúncios!",
        "attachments": [
            {
                "text": f"{ad.brand} {ad.model} - R$ {ad.price}",
                "color": "good"
            }
            for ad in ads[:5]
        ]
    }
    
    requests.post(webhook_url, json=message)
```

## 🔒 Segurança

### 1. Validar inputs

```python
def sanitize_url(url):
    """Valida URL do grupo"""
    if not url.startswith('https://www.facebook.com/groups/'):
        raise ValueError(f"URL inválida: {url}")
    return url
```

### 2. Rate limiting robusto

```python
from time import time, sleep

class RateLimiter:
    def __init__(self, calls_per_minute=60):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    def wait_if_needed(self):
        now = time()
        # Remove chamadas antigas (>1 minuto)
        self.calls = [c for c in self.calls if now - c < 60]
        
        if len(self.calls) >= self.calls_per_minute:
            sleep_time = 60 - (now - self.calls[0])
            if sleep_time > 0:
                sleep(sleep_time)
        
        self.calls.append(now)
```

## 🐛 Debug

### 1. Modo verbose

```python
# Em .env
DEBUG=true
LOG_LEVEL=DEBUG
```

```python
# No código
import logging
log_level = logging.DEBUG if os.getenv('DEBUG') == 'true' else logging.INFO
logging.basicConfig(level=log_level)
```

### 2. Salvar análises problemáticas

```python
def analyze_with_fallback(post):
    try:
        return analyzer.analyze_post(post)
    except Exception as e:
        # Salvar post problemático
        error_dir = "data/errors"
        os.makedirs(error_dir, exist_ok=True)
        
        with open(f"{error_dir}/{post['id']}.json", 'w') as f:
            json.dump({
                'post': post,
                'error': str(e)
            }, f)
        
        # Retornar análise vazia
        return {'is_advertisement': False, 'error': str(e)}
```

## 📈 Monitoramento

```python
import time

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
    
    def track(self, operation):
        def decorator(func):
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start
                
                if operation not in self.metrics:
                    self.metrics[operation] = []
                self.metrics[operation].append(duration)
                
                return result
            return wrapper
        return decorator
    
    def report(self):
        for op, times in self.metrics.items():
            avg = sum(times) / len(times)
            print(f"{op}: {avg:.2f}s (avg), {sum(times):.2f}s (total)")

# Uso
monitor = PerformanceMonitor()

@monitor.track('scraping')
def scrape():
    pass

@monitor.track('analysis')
def analyze():
    pass
```
