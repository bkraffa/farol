# ☁️ Guia Cloud Deployment - Opções Completas

## Visão Geral das Opções

| Opção | MongoDB | App | Custo/mês | Complexidade | Recomendado |
|-------|---------|-----|-----------|--------------|-------------|
| **1. Atlas + AWS Lambda** | Atlas Free | Lambda Free | ~$0-5 | Baixa | ✅ Iniciantes |
| **2. Atlas + Fly.io** | Atlas Free | Fly Free | ~$0 | Baixa | ✅ Hobby |
| **3. Atlas + Railway** | Atlas Free | Railway $5 | ~$5 | Baixa | ⭐ Melhor |
| **4. Atlas + Render** | Atlas Free | Render Free | ~$0 | Baixa | ✅ Simples |
| **5. Atlas + VPS** | Atlas Free | VPS $5-10 | ~$5-10 | Média | ✅ Controle |
| **6. Atlas + Heroku** | Atlas Free | Heroku $7 | ~$7 | Baixa | ⚠️ Caro |

## 🌟 Opção Recomendada: MongoDB Atlas + Railway

### Por que Railway?

- ✅ Deploy super simples (conecta GitHub)
- ✅ Tier gratuito generoso
- ✅ Cron jobs nativos
- ✅ Logs em tempo real
- ✅ Variáveis de ambiente fáceis
- ✅ Zero configuração

### Setup Completo

#### 1. MongoDB Atlas (5 min)

```bash
# 1. Criar conta
https://mongodb.com/cloud/atlas/register

# 2. Criar cluster M0 (free)
- Região: us-east-1 (mais próximo do Railway)
- Nome: kitesurf-cluster

# 3. Database Access
- Username: kitesurf_user
- Password: (gerar senha forte)

# 4. Network Access
- Add IP: 0.0.0.0/0 (permite qualquer IP)
  ⚠️ Produção: especificar IPs

# 5. Connect
- Copiar connection string:
mongodb+srv://kitesurf_user:<password>@cluster0.xxxxx.mongodb.net/
```

#### 2. Preparar Projeto

```bash
# 1. Criar Procfile
cat > Procfile << EOF
# Worker para scraping incremental
worker: python scripts/run_incremental.py
EOF

# 2. Criar railway.json para cron
cat > railway.json << EOF
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "sleepOnStart": false,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF

# 3. Push para GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/seu-usuario/kitesurf-scraper
git push -u origin main
```

#### 3. Deploy no Railway

```bash
# 1. Criar conta: https://railway.app
# 2. "New Project" → "Deploy from GitHub repo"
# 3. Selecionar seu repositório
# 4. Adicionar variáveis de ambiente:
```

**Variáveis:**
```env
APIFY_API_TOKEN=seu_token
OPENAI_API_KEY=sua_chave
OPENAI_MODEL=gpt-4o-mini
MONGODB_URI=mongodb+srv://kitesurf_user:senha@cluster0.xxxxx.mongodb.net/kitesurf
```

#### 4. Configurar Cron

**Opção A: Railway Cron (nativo)**
```bash
# No Railway dashboard:
# Settings → Cron → Add Schedule
# Schedule: 0 8,20 * * *
# Command: python scripts/run_incremental.py
```

**Opção B: Serviço externo**
```bash
# Usar cron-job.org (gratuito)
https://cron-job.org

# Criar webhook no Railway
# Endpoint: /run-scraping
# Schedule: 0 8,20 * * *
```

#### 5. Testar

```bash
# Ver logs no Railway dashboard
# Ou via CLI
railway logs
```

## 🚀 Alternativas Rápidas

### Opção 1: AWS Lambda + EventBridge

**Custo:** ~$0-1/mês

```bash
# 1. Preparar deployment package
pip install -r requirements.txt -t package/
cp -r src scripts package/
cd package && zip -r ../deployment.zip . && cd ..

# 2. Criar Lambda function
aws lambda create-function \
  --function-name kitesurf-scraper \
  --runtime python3.11 \
  --handler scripts.run_incremental.main \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --zip-file fileb://deployment.zip \
  --timeout 900 \
  --memory-size 1024 \
  --environment Variables="{MONGODB_URI=...,OPENAI_API_KEY=...}"

# 3. Criar EventBridge rule (cron)
aws events put-rule \
  --name kitesurf-scraper-schedule \
  --schedule-expression "cron(0 8,20 * * ? *)"

# 4. Conectar rule com Lambda
aws lambda add-permission \
  --function-name kitesurf-scraper \
  --statement-id scheduled-execution \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com
```

### Opção 2: Fly.io

**Custo:** $0 (free tier)

```bash
# 1. Instalar CLI
curl -L https://fly.io/install.sh | sh

# 2. Login
fly auth login

# 3. Launch app
fly launch --name kitesurf-scraper

# 4. Adicionar variáveis
fly secrets set MONGODB_URI="..." OPENAI_API_KEY="..."

# 5. Deploy
fly deploy

# 6. Schedule com fly.toml
cat > fly.toml << EOF
[[services]]
  processes = ["cron"]
  
[[services.cron]]
  schedule = "0 8,20 * * *"
  command = "python scripts/run_incremental.py"
EOF
```

### Opção 3: Render

**Custo:** $0 (free tier)

```bash
# 1. Criar conta: https://render.com
# 2. New → Background Worker
# 3. Connect GitHub
# 4. Configure:
#    - Build Command: pip install -r requirements.txt
#    - Start Command: python scripts/run_incremental.py
# 5. Adicionar Environment Variables
# 6. Enable Cron:
#    - Cron Expression: 0 8,20 * * *
```

## 🏠 VPS (DigitalOcean, Linode, etc)

**Custo:** $5-10/mês  
**Controle:** Total

### Setup Completo

```bash
# 1. Criar droplet Ubuntu 22.04 ($5/mês)
# 2. SSH no servidor
ssh root@seu-ip

# 3. Setup inicial
apt update && apt upgrade -y
apt install python3 python3-pip git -y

# 4. Clone projeto
cd /opt
git clone https://github.com/seu-usuario/kitesurf-scraper
cd kitesurf-scraper

# 5. Setup Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Configurar .env
nano config/.env
# (adicionar suas chaves)

# 7. Testar
python scripts/run_incremental.py

# 8. Setup cron
crontab -e
# Adicionar:
0 8,20 * * * cd /opt/kitesurf-scraper && /opt/kitesurf-scraper/venv/bin/python scripts/run_incremental.py >> logs/cron.log 2>&1

# 9. Setup systemd (opcional, para executar como serviço)
cat > /etc/systemd/system/kitesurf.service << EOF
[Unit]
Description=Kitesurf Scraper
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kitesurf-scraper
ExecStart=/opt/kitesurf-scraper/venv/bin/python scripts/run_incremental.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl enable kitesurf.service
```

## 🐳 Docker + Cloud Run (Google Cloud)

**Custo:** ~$0-5/mês

```bash
# 1. Criar Dockerfile
cat > Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "scripts/run_incremental.py"]
EOF

# 2. Build e push
docker build -t gcr.io/PROJECT_ID/kitesurf-scraper .
docker push gcr.io/PROJECT_ID/kitesurf-scraper

# 3. Deploy no Cloud Run
gcloud run deploy kitesurf-scraper \
  --image gcr.io/PROJECT_ID/kitesurf-scraper \
  --platform managed \
  --region us-central1 \
  --set-env-vars MONGODB_URI=...,OPENAI_API_KEY=...

# 4. Schedule com Cloud Scheduler
gcloud scheduler jobs create http kitesurf-job \
  --schedule="0 8,20 * * *" \
  --uri="https://kitesurf-scraper-xxx.run.app" \
  --http-method=POST
```

## 📊 Comparação Detalhada

### Performance

| Opção | Latência | CPU | RAM | Storage |
|-------|----------|-----|-----|---------|
| Lambda | Baixa | 1 vCPU | 1GB | Ephemeral |
| Railway | Baixa | 0.5 vCPU | 512MB | 1GB |
| Fly.io | Baixa | Shared | 256MB | 3GB |
| Render | Média | Shared | 512MB | 1GB |
| VPS | Baixa | 1 vCPU | 1GB | 25GB |
| Cloud Run | Baixa | 1 vCPU | 2GB | Ephemeral |

### Facilidade

| Opção | Setup | Deploy | Manutenção |
|-------|-------|--------|------------|
| Railway | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Render | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Fly.io | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Lambda | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| VPS | ⭐⭐ | ⭐⭐ | ⭐⭐ |
| Cloud Run | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

## 🎯 Recomendação por Caso

### Hobby/Teste
→ **Railway** ou **Render** (free tier)

### Produção Pequena
→ **Railway** ($5/mês) + MongoDB Atlas (free)

### Produção Média
→ **VPS** ($10/mês) + MongoDB Atlas ($57/mês)

### Produção Grande
→ **Kubernetes** (AWS EKS) + MongoDB Atlas (paid tier)

## 🔒 Segurança

### Checklist

- [ ] Variáveis de ambiente (nunca commitar .env)
- [ ] MongoDB: IP whitelist em produção
- [ ] MongoDB: Senha forte
- [ ] HTTPS obrigatório
- [ ] Rate limiting
- [ ] Logs monitorados
- [ ] Backup automático
- [ ] Alertas configurados

### Implementar

```python
# Rate limiting
from functools import wraps
import time

def rate_limit(max_calls=10, period=60):
    calls = []
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [c for c in calls if now - c < period]
            if len(calls) >= max_calls:
                time.sleep(period - (now - calls[0]))
            calls.append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(max_calls=50, period=3600)
def analyze_post(post):
    # ...
```

## 📈 Monitoramento

### Opções

1. **Railway/Render**: Logs nativos
2. **Sentry**: Error tracking
3. **Datadog**: APM completo
4. **CloudWatch**: AWS monitoring
5. **MongoDB Atlas**: DB monitoring

### Setup Sentry

```bash
pip install sentry-sdk

# No código
import sentry_sdk
sentry_sdk.init(dsn="https://xxx@sentry.io/xxx")
```

## 🎉 Deploy em 10 Minutos (TL;DR)

```bash
# 1. MongoDB Atlas
# - Criar conta + cluster M0
# - Copiar connection string

# 2. GitHub
git init && git add . && git commit -m "init" && git push

# 3. Railway.app
# - Conectar GitHub
# - Add env vars
# - Enable cron: 0 8,20 * * *

# Pronto! ✅
```

---

**Recomendação final:** MongoDB Atlas (free) + Railway ($0-5/mês) = Setup ideal para começar! 🚀
