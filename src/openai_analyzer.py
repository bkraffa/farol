"""
Analisador de posts usando OpenAI GPT-4 Vision
"""
import os
import json
import logging
import base64
import requests
from typing import Dict, Any, List, Optional
from openai import OpenAI

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

IMPORTANTE:
- Analise TEXTO, IMAGENS e COMENTÁRIOS para extrair todas as informações
- Preços em comentários são muito comuns
- Informações técnicas podem estar nas imagens
- Seja criterioso: apenas identifique como anúncio se realmente estiver vendendo algo
- Se não tiver certeza de algum campo, deixe como null
- Extraia informações de contato quando disponíveis
"""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        
    def analyze_post(
        self, 
        post_data: Dict[str, Any],
        download_images: bool = True
    ) -> Dict[str, Any]:
        """
        Analisa um post do Facebook e extrai informações estruturadas
        
        Args:
            post_data: Dados do post (do Apify)
            download_images: Se deve baixar e incluir imagens na análise
            
        Returns:
            Dicionário com análise estruturada
        """
        try:
            # Preparar dados do post
            post_info = self._prepare_post_data(post_data)
            
            # Preparar imagens se disponíveis
            image_urls = []
            if download_images:
                image_urls = self._extract_image_urls(post_data)
            
            # Criar prompt
            user_prompt = self._create_analysis_prompt(post_info, image_urls)
            
            # Fazer chamada para OpenAI
            response = self._call_openai(user_prompt, image_urls)
            
            # Parsear resposta
            analysis = self._parse_response(response)
            
            # Adicionar metadados
            analysis["post_id"] = post_data.get("id") or post_data.get("legacyId")
            analysis["post_url"] = post_data.get("url")
            
            logger.info(
                f"Post analisado: {analysis['post_id']} - "
                f"Anúncio: {analysis['is_advertisement']}"
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro ao analisar post: {str(e)}")
            return {
                "error": str(e),
                "is_advertisement": False,
                "confidence_score": 0.0
            }
    
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
        
        return {
            "title": title,
            "text": text,
            "location": location,
            "price": price,
            "comments": comments,
            "user_name": post_data.get("user", {}).get("name", "")
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
    
    def _extract_comments(self, post_data: Dict) -> List[str]:
        """Extrai texto dos comentários"""
        comments = []
        top_comments = post_data.get("topComments", [])
        
        for comment in top_comments[:10]:  # Limitar a 10 comentários
            if "text" in comment:
                comments.append(comment["text"])
        
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

COMENTÁRIOS ({len(post_info['comments'])}):
"""
        
        for i, comment in enumerate(post_info['comments'][:10], 1):
            prompt += f"\n{i}. {comment}"
        
        if image_urls:
            prompt += f"\n\n[{len(image_urls)} imagens anexadas para análise visual]"
        
        prompt += """

Retorne um JSON válido com a seguinte estrutura:
{
  "is_advertisement": boolean,
  "confidence_score": float (0-1),
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
  "contact_info": string | null,
  "contact_preferences": [string],
  "extracted_from_text": boolean,
  "extracted_from_images": boolean,
  "extracted_from_comments": boolean,
  "analysis_notes": string | null,
  "keywords": [string]
}

INSTRUÇÕES:
- Analise TODO o conteúdo: texto, imagens e comentários
- Preços frequentemente aparecem nos comentários
- Informações técnicas podem estar nas imagens (tamanhos, marcas, modelos)
- Se não for um anúncio de venda, marque is_advertisement como false
- Extraia o máximo de informações possível
- Seja preciso com preços (converta se necessário, ex: R7500 = 7500.0)
- Para localização, extraia cidade e estado (sigla)
- Identifique marca e modelo mesmo que não explícitos
- Liste itens adicionais (ex: "inclui barra", "com bag", etc)
"""
        
        return prompt
    
    def _call_openai(
        self, 
        prompt: str, 
        image_urls: List[str]
    ) -> str:
        """Faz chamada para OpenAI API"""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]
        
        # Preparar conteúdo da mensagem
        content = [{"type": "text", "text": prompt}]
        
        # Adicionar imagens se disponíveis
        for url in image_urls:
            content.append({
                "type": "image_url",
                "image_url": {"url": url, "detail": "low"}
            })
        
        messages.append({"role": "user", "content": content})
        
        # Fazer chamada
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
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
                logger.info(f"Progresso: {i}/{total} - Anúncios encontrados: {ads_found}")
        
        ads_found = sum(1 for r in results if r.get("is_advertisement"))
        logger.info(f"Análise concluída: {ads_found}/{total} anúncios identificados")
        
        return results
