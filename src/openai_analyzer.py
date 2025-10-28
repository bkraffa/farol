"""
Analisador de posts usando OpenAI GPT-4 Vision
Com suporte a múltiplos anúncios e score de revenda
"""
import os
import json
import logging
import base64
import requests
from typing import Dict, Any, List, Optional
from openai import OpenAI
from src.resale_scorer import ResaleScorer

logger = logging.getLogger(__name__)


class OpenAIAnalyzer:
    """Analisador de anúncios de equipamentos usando GPT-4 Vision"""
    
    SYSTEM_PROMPT = """Você é um especialista em equipamentos de kitesurfe e análise de anúncios de marketplace.
Sua tarefa é analisar posts de grupos do Facebook para identificar anúncios de venda de equipamentos e extrair informações estruturadas.

Equipamentos de kitesurfe incluem:
- Kites (pipas): Duotone, North, Cabrinha, Core, Slingshot, Ozone, Naish, etc.
- Pranchas (boards): twintip, direcional, foil
- Barras (bars/control bars)
- Trapézios (harness)
- Roupas (wetsuits, lycras)
- Acessórios (bombas, leash, etc)

Marcas comuns: Duotone, North Kiteboarding, Cabrinha, Core, Slingshot, Ozone, Naish, F-One, Airush, Liquid Force, etc.

🎯 CRITÉRIOS PARA IDENTIFICAR ANÚNCIOS (SEJA LIBERAL, NÃO CONSERVADOR):

✅ É ANÚNCIO se:
- Menciona "vendo", "venda", "à venda", "for sale", "selling"
- Tem PREÇO + descrição de equipamento (ex: "Kite 12m R$ 4000")
- Tem TÍTULO do equipamento + preço (ex: "Prancha Duotone R$ 3500")
- Tem fotos de equipamento + contato (telefone/WhatsApp)
- É post do Facebook Marketplace (tem campo "price")
- Menciona "negociável", "aceito propostas", "valor"
- Tem especificações técnicas + preço (ex: "12m 2024 R$ 5000")

❌ NÃO é anúncio se:
- É pergunta ("alguém tem?", "onde comprar?")
- É pedido ("procuro", "quero comprar", "WTB")
- É discussão sobre equipamento sem intenção de venda
- É foto de session/prática sem menção de venda
- É notícia ou informação geral

⚠️ ATENÇÃO ESPECIAL - MÚLTIPLOS ANÚNCIOS:
Um mesmo post pode conter VÁRIOS equipamentos à venda.

🔥 IMPORTANTE - SEJA MAIS LIBERAL NA DETECÇÃO:
- Se há QUALQUER indicação de venda, marque como anúncio
- Se há preço + equipamento, É ANÚNCIO
- Na dúvida, prefira marcar como anúncio (is_advertisement: true)
- Use confidence_score baixo se não tiver certeza
- Analise TEXTO, IMAGENS e COMENTÁRIOS
- Preços podem estar em comentários
- Extraia informações de contato (telefone/WhatsApp)
"""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        
    def analyze_post(
        self, 
        post_data: Dict[str, Any],
        download_images: bool = True
    ) -> Dict[str, Any]:
        try:
            post_info = self._prepare_post_data(post_data)

            # NOVO: preferir imagens locais já baixadas pelo scraper
            if download_images:
                if "local_images" in post_data and post_data["local_images"]:
                    image_sources = {
                        "type": "local",
                        "paths": post_data["local_images"]
                    }
                else:
                    # fallback: ainda tenta URLs diretas
                    image_sources = {
                        "type": "remote",
                        "urls": self._extract_image_urls(post_data)
                    }
            else:
                image_sources = {"type": "none"}

            user_prompt = self._create_analysis_prompt(
                post_info,
                # só pra log, comprimento etc
                (image_sources.get("paths") if image_sources["type"] == "local" else
                image_sources.get("urls", []))
            )

            response = self._call_openai(user_prompt, image_sources)

            analysis = self._parse_response(response)

            analysis["post_id"] = post_data.get("id") or post_data.get("legacyId")
            analysis["post_url"] = post_data.get("url")

            if analysis.get('is_advertisement'):
                analysis['resale_score'] = self._calculate_resale_score(
                    analysis,
                    post_info
                )

            logger.info(
                f"Post analisado: {analysis['post_id']} - "
                f"Anúncio: {analysis['is_advertisement']}"
                + (f" - Score: {analysis.get('resale_score', {}).get('total_score', 0):.1f}" 
                if analysis.get('is_advertisement') else "")
            )

            return analysis

        except Exception as e:
            logger.error(f"Erro ao analisar post: {str(e)}")
            return {
                "error": str(e),
                "is_advertisement": False,
                "confidence_score": 0.0
            }

    def _encode_image_base64_uri(self, file_path: str) -> Optional[str]:
        """
        Lê a imagem local e devolve um data URI base64:
        "data:image/jpeg;base64,AAAA..."
        Se der erro, retorna None.
        """
        try:
            with open(file_path, "rb") as f:
                raw = f.read()
            b64 = base64.b64encode(raw).decode("utf-8")

            # heurística simples pra mimetype
            mime = "image/jpeg"
            lower = file_path.lower()
            if lower.endswith(".png"):
                mime = "image/png"
            elif lower.endswith(".webp"):
                mime = "image/webp"
            elif lower.endswith(".jpg") or lower.endswith(".jpeg"):
                mime = "image/jpeg"

            return f"data:{mime};base64,{b64}"
        except Exception as e:
            logger.warning(f"Falha ao base64 {file_path}: {e}")
            return None

    
    def _prepare_post_data(self, post_data: Dict) -> Dict:
        """Prepara dados do post para análise"""
        # Tentar pegar do sharedPost se existir (post compartilhado)
        if "sharedPost" in post_data and post_data["sharedPost"]:
            shared = post_data["sharedPost"]
            text = shared.get("text", "")
            title = shared.get("title", "")
            location = shared.get("location", "")
            price = shared.get("price", "")
        else:
            text = post_data.get("text", "")
            title = post_data.get("title", "")
            location = post_data.get("location", "")
            price = post_data.get("price", "")
        
        # Obter comentários
        comments = self._extract_comments(post_data)
        
        # Obter métricas de engajamento
        likes_count = post_data.get("likesCount", 0) or post_data.get("reactionLikeCount", 0)
        comments_count = post_data.get("commentsCount", 0)
        shares_count = post_data.get("sharesCount", 0)
        
        return {
            "title": title,
            "text": text,
            "location": location,
            "price": price,
            "comments": comments,
            "user_name": post_data.get("user", {}).get("name", ""),
            "likes_count": likes_count,
            "comments_count": comments_count,
            "shares_count": shares_count
        }
    
    def _extract_image_urls(self, post_data: Dict) -> List[str]:
        """Extrai URLs das imagens do post"""
        image_urls = []
        
        # Pegar imagens do sharedPost se existir
        attachments = []
        if "sharedPost" in post_data and post_data["sharedPost"]:
            attachments = post_data["sharedPost"].get("attachments", [])
        else:
            attachments = post_data.get("attachments", [])
        
        for attachment in attachments:
            if attachment.get("__typename") == "Photo":
                # Tentar pegar a melhor qualidade disponível
                if "photo_image" in attachment:
                    image_urls.append(attachment["photo_image"]["uri"])
                elif "image" in attachment:
                    image_urls.append(attachment["image"]["uri"])
                elif "thumbnail" in attachment:
                    image_urls.append(attachment["thumbnail"])
        
        # Limitar a 4 imagens para não estourar o token limit
        return image_urls[:4]
    
    def _extract_comments(self, post_data: Dict) -> List[Dict]:
        """Extrai texto dos comentários com metadados"""
        comments = []
        top_comments = post_data.get("topComments", [])
        
        for comment in top_comments[:15]:  # Limitar a 15 comentários
            if "text" in comment:
                comments.append({
                    "text": comment["text"],
                    "author": comment.get("author", {}).get("name", "Unknown")
                })
        
        return comments
    
    def _create_analysis_prompt(
        self, 
        post_info: Dict,
        image_urls: List[str]
    ) -> str:
        """Cria o prompt para análise"""
        prompt = f"""Analise este post de grupo do Facebook e extraia informações estruturadas.

TÍTULO: {post_info['title']}

TEXTO DO POST:
{post_info['text']}

LOCALIZAÇÃO: {post_info['location']}
PREÇO MENCIONADO: {post_info['price']}

AUTOR: {post_info['user_name']}

ENGAJAMENTO:
- Likes: {post_info['likes_count']}
- Comentários: {post_info['comments_count']}
- Compartilhamentos: {post_info['shares_count']}

COMENTÁRIOS ({len(post_info['comments'])}):
"""
        
        for i, comment in enumerate(post_info['comments'][:15], 1):
            prompt += f"\n{i}. {comment['author']}: {comment['text']}"
        
        if image_urls:
            prompt += f"\n\n[{len(image_urls)} imagens anexadas para análise visual]"
        
        prompt += """

🎯 EXEMPLOS DE ANÚNCIOS (marque is_advertisement: true):

✅ "Vendo kite Duotone Rebel 12m 2024 - R$ 5000"
✅ "Prancha North Jaime 136x41. Valor: R$ 3500. Whats (85)99999"
✅ Post do Marketplace com campo price="R$4,000"
✅ "Barra Duotone Click 2024 impecável. 2500 reais"
✅ "Kit: 2 kites + prancha. R$ 10.000 negociável"

❌ EXEMPLOS DE NÃO-ANÚNCIOS (marque is_advertisement: false):

❌ "Alguém tem uma barra usada pra vender?" (pedido/WTB)
❌ "Procuro kite 12m, até R$ 4000" (WTB)
❌ "Session incrível hoje!" (relato)
❌ "Qual kite recomendam?" (pergunta)

⚠️ NA DÚVIDA: Se tem preço + equipamento = É ANÚNCIO!

⚠️ MÚLTIPLOS ITENS:
Se o post anuncia VÁRIOS equipamentos, identifique:
- has_multiple_items: true
- item_count: número de itens
- additional_items_detailed: lista descritiva de cada item

Retorne um JSON válido com a seguinte estrutura:
{
  "is_advertisement": boolean,
  "confidence_score": float (0-1),
  "has_multiple_items": boolean,
  "item_count": integer,
  "equipment_type": "kite" | "board" | "bar" | "harness" | "wetsuit" | "pump" | "accessories" | "complete_set" | "other",
  "brand": string | null,
  "model": string | null,
  "year": integer | null,
  "size": string | null,
  "condition": "novo" | "seminovo" | "bom_estado" | "usado" | "precisa_reparo" | "desconhecido",
  "has_repair": boolean,
  "repair_description": string | null,
  "price": float | null,
  "currency": "BRL",
  "price_negotiable": boolean,
  "city": string | null,
  "state": string | null (sigla: CE, SP, RJ, etc),
  "description": string,
  "additional_items": [string],
  "additional_items_detailed": [string],
  "contact_info": string | null,
  "contact_preferences": [string],
  "extracted_from_text": boolean,
  "extracted_from_images": boolean,
  "extracted_from_comments": boolean,
  "comment_interest_level": "high" | "medium" | "low" | "negative",
  "analysis_notes": string | null,
  "keywords": [string]
}

INSTRUÇÕES FINAIS:
1. **SEJA LIBERAL NA DETECÇÃO**: Se há QUALQUER indicação de venda (preço + equipamento), marque is_advertisement: true
2. Analise TODO o conteúdo: texto, imagens e comentários
3. Preços frequentemente aparecem nos comentários
4. Informações técnicas podem estar nas imagens
5. Posts do Facebook Marketplace (com campo "price") SÃO SEMPRE anúncios
6. Se texto menciona "vendo", "venda", "à venda" + equipamento = É ANÚNCIO
7. Se há preço + descrição de equipamento = É ANÚNCIO (mesmo sem "vendo")
8. Extraia o máximo de informações possível
9. Seja preciso com preços (converta se necessário, ex: R7500 = 7500.0)
10. Para localização, extraia cidade e estado (sigla)
11. Identifique marca e modelo mesmo que não explícitos
12. Liste itens adicionais (ex: "inclui barra", "com bag")
13. Se houver múltiplos equipamentos, liste TODOS em additional_items_detailed
14. Analise o TIPO de comentários: perguntas sobre preço = alto interesse

🔥 LEMBRE-SE: Na dúvida, PREFIRA marcar como anúncio (is_advertisement: true) com confidence_score baixo.
"""
        
        return prompt
    
    def _call_openai(
        self, 
        prompt: str, 
        image_sources: Dict[str, Any],
    ) -> str:
        """
        Faz chamada pra OpenAI. 
        image_sources pode ser:
        {"type": "local", "paths": ["/abs/path/img0.jpg", ...]}
        {"type": "remote", "urls": ["https://..."]}
        {"type": "none"}
        """
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]

        # monta o "content" principal
        content = [{"type": "text", "text": prompt}]

        # anexar imagens
        valid_images = 0

        if image_sources["type"] == "local":
            for p in image_sources["paths"][:4]:
                data_uri = self._encode_image_base64_uri(p)
                if data_uri:
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": data_uri,
                            "detail": "low"
                        }
                    })
                    valid_images += 1

        elif image_sources["type"] == "remote":
            for url in image_sources["urls"][:4]:
                # só aceita links http/https
                if url and ("http://" in url or "https://" in url):
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": url, "detail": "low"}
                    })
                    valid_images += 1

        # warning leve se prometeu imagem mas não conseguiu anexar
        if image_sources["type"] != "none" and valid_images == 0:
            logger.warning("Nenhuma imagem válida encontrada, analisando apenas texto")

        messages.append({"role": "user", "content": content})

        # retry simples
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=2500
                )
                return response.choices[0].message.content

            except Exception as e:
                error_msg = str(e)

                # se o erro for relacionado a imagens, tenta degradar pra só texto
                if "invalid_image_url" in error_msg.lower() and valid_images > 0:
                    logger.warning("Erro com imagens, tentando novamente só com texto...")
                    # remove qualquer bloco type=image_url
                    content_no_img = [c for c in content if c.get("type") != "image_url"]
                    messages[-1]["content"] = content_no_img
                    valid_images = 0
                    continue

                if attempt == max_retries - 1:
                    raise

                logger.warning(f"Tentativa {attempt + 1} falhou, tentando novamente...")

        raise Exception("Falha após múltiplas tentativas")

    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parseia resposta JSON da OpenAI"""
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear resposta JSON: {str(e)}")
            logger.error(f"Resposta: {response}")
            return {
                "is_advertisement": False,
                "confidence_score": 0.0,
                "error": "Failed to parse OpenAI response"
            }
    
    def _calculate_resale_score(
        self,
        analysis: Dict[str, Any],
        post_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calcula score de potencial de revenda"""
        try:
            # Extrair dados necessários
            equipment_type = analysis.get('equipment_type', 'other')
            brand = analysis.get('brand', '')
            year = analysis.get('year', 2020)
            price = analysis.get('price', 0.0)
            condition = analysis.get('condition', 'desconhecido')
            has_repair = analysis.get('has_repair', False)
            
            # Extrair comentários como lista de strings
            comments = [c['text'] for c in post_info.get('comments', [])]
            comments_count = post_info.get('comments_count', 0)
            likes_count = post_info.get('likes_count', 0)
            
            # Calcular score
            score = ResaleScorer.calculate_score(
                equipment_type=equipment_type,
                brand=brand or '',
                year=year or 2020,
                price=price or 0.0,
                condition=condition,
                has_repair=has_repair,
                comments=comments,
                comments_count=comments_count,
                likes_count=likes_count
            )
            
            return score
            
        except Exception as e:
            logger.error(f"Erro ao calcular score de revenda: {str(e)}")
            return {
                'total_score': 0.0,
                'classification': 'Erro ao calcular',
                'factors': {},
                'recommendation': 'Não foi possível calcular o score'
            }
    
    def analyze_batch(
        self,
        posts: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Analisa múltiplos posts em lote
        
        Args:
            posts: Lista de posts para analisar
            max_concurrent: Máximo de análises concorrentes
            
        Returns:
            Lista de análises
        """
        results = []
        total = len(posts)
        
        logger.info(f"Iniciando análise de {total} posts")
        
        for i, post in enumerate(posts, 1):
            logger.info(f"Analisando post {i}/{total}")
            analysis = self.analyze_post(post)
            results.append(analysis)
            
            # Log progress
            if i % 10 == 0:
                ads_found = sum(1 for r in results if r.get("is_advertisement"))
                avg_score = sum(
                    r.get('resale_score', {}).get('total_score', 0) 
                    for r in results if r.get('is_advertisement')
                ) / max(ads_found, 1)
                logger.info(
                    f"Progresso: {i}/{total} - Anúncios: {ads_found} - "
                    f"Score médio: {avg_score:.1f}/100"
                )
        
        ads_found = sum(1 for r in results if r.get("is_advertisement"))
        logger.info(f"Análise concluída: {ads_found}/{total} anúncios identificados")
        
        return results