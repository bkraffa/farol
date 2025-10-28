"""
Cliente para scraping do Facebook via Apify
"""
import os
import json
import logging
import requests
from typing import List, Dict, Any
from datetime import datetime
from apify_client import ApifyClient

logger = logging.getLogger(__name__)


class ApifyFacebookScraper:
    """Cliente para scraping de grupos do Facebook usando Apify"""
    
    def __init__(self, api_token: str, media_dir: str = "data/media"):
        self.client = ApifyClient(api_token)
        self.actor_id = "apify/facebook-groups-scraper"
        self.media_dir = media_dir
        os.makedirs(self.media_dir, exist_ok=True)

    def run_historical_scrape(
        self, 
        group_urls: List[str],
        days_back: int = 730  # 2 anos
    ) -> Dict[str, Any]:
        logger.info(f"Iniciando scraping histórico de {len(group_urls)} grupos")
        logger.info(f"Buscando posts dos últimos {days_back} dias")
        
        run_input = {
            "startUrls": [{"url": url} for url in group_urls],
            "viewOption": "CHRONOLOGICAL",
            "onlyPostsNewerThan": f"{days_back} days",
            "maxPosts": 10000,
            "resultsLimit": 10000,
        }
        
        return self._run_scraper(run_input, "historical")
    
    def run_incremental_scrape(
        self,
        group_urls: List[str],
        hours_back: int = 12
    ) -> Dict[str, Any]:
        logger.info(f"Iniciando scraping incremental de {len(group_urls)} grupos")
        logger.info(f"Buscando posts das últimas {hours_back} horas")
        
        run_input = {
            "startUrls": [{"url": url} for url in group_urls],
            "viewOption": "CHRONOLOGICAL",
            "onlyPostsNewerThan": f"{hours_back} hours",
            "maxPosts": 500,
            "resultsLimit": 500,
        }
        
        return self._run_scraper(run_input, "incremental")
    
    def _run_scraper(self, run_input: Dict[str, Any], job_type: str) -> Dict[str, Any]:
        """
        Executa o actor, baixa imagens, devolve posts enriquecidos
        """
        try:
            logger.info(f"Executando Apify actor: {self.actor_id}")
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            
            dataset_id = run["defaultDatasetId"]
            items = list(self.client.dataset(dataset_id).iterate_items())

            logger.info(f"Scraping concluído: {len(items)} posts coletados")

            # baixa imagens agora
            enriched_items = self._download_and_attach_images(items)

            return {
                "job_type": job_type,
                "run_id": run["id"],
                "status": run["status"],
                "started_at": run["startedAt"],
                "finished_at": run["finishedAt"],
                "stats": run.get("stats", {}),
                "items": enriched_items,
                "total_items": len(enriched_items),
            }
        except Exception as e:
            logger.error(f"Erro ao executar scraper: {str(e)}")
            raise

    def _extract_image_urls_from_post(self, post_data: Dict[str, Any]) -> List[str]:
        """
        Coleta até 4 melhores URLs de imagem do post/sharedPost.
        Remove duplicatas.
        """
        urls = []

        post_like = post_data.get("sharedPost") or post_data
        attachments = post_like.get("attachments", [])

        for att in attachments:
            if att.get("__typename") == "Photo":
                if "photo_image" in att and "uri" in att["photo_image"]:
                    urls.append(att["photo_image"]["uri"])
                if "image" in att and "uri" in att["image"]:
                    urls.append(att["image"]["uri"])
                if "thumbnail" in att:
                    urls.append(att["thumbnail"])

        # dedupe mas manter ordem -> truquezinho com dict.fromkeys
        urls = list(dict.fromkeys(urls))

        return urls[:4]

    def _safe_download_image(self, url: str, dest_path: str) -> bool:
        """
        Baixa imagem da CDN do Facebook com headers tipo navegador.
        Loga status. Faz fallback sem querystring.
        """
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/127.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.facebook.com/",
            "Sec-Fetch-Dest": "image",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site",
            "Connection": "keep-alive",
        }

        candidates = [url]
        if "?" in url:
            base_no_query = url.split("?", 1)[0]
            if base_no_query.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                candidates.append(base_no_query)

        for cand in candidates:
            for attempt in range(2):
                try:
                    resp = requests.get(
                        cand,
                        headers=headers,
                        timeout=10,
                        stream=True,
                    )

                    ctype = resp.headers.get("Content-Type", "")
                    if resp.status_code == 200 and ctype.startswith("image"):
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        with open(dest_path, "wb") as f:
                            for chunk in resp.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        logger.info(f"[img ok] {cand} -> {dest_path}")
                        return True
                    else:
                        logger.warning(
                            f"[img fail] status={resp.status_code} ctype={ctype} url={cand}"
                        )
                except Exception as e:
                    logger.warning(f"[img exc] {cand} -> {e}")

        return False

    def _download_and_attach_images(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Para cada post:
          - cria pasta única data/media/<post_id>/
          - tenta baixar até 4 imagens
          - adiciona:
              post["image_urls"] (remotos)
              post["local_images"] (paths salvos OK)
              post["media_dir"]
              post["download_errors"] (opcional p/ debug)
        """
        enriched = []

        for post in posts:
            post_id = (
                post.get("id")
                or post.get("legacyId")
                or f"noid_{datetime.utcnow().strftime('%Y%m%d_%H%M%S%f')}"
            )

            post_dir = os.path.join(self.media_dir, str(post_id))
            os.makedirs(post_dir, exist_ok=True)

            img_urls = self._extract_image_urls_from_post(post)

            local_paths = []
            errors = []

            for idx, img_url in enumerate(img_urls):
                # tenta inferir extensão
                ext = ".jpg"
                lower = img_url.lower()
                if ".png" in lower:
                    ext = ".png"
                elif ".jpeg" in lower:
                    ext = ".jpeg"
                elif ".webp" in lower:
                    ext = ".webp"

                filename = f"img_{idx}{ext}"
                dest_path = os.path.join(post_dir, filename)

                ok = self._safe_download_image(img_url, dest_path)
                if ok:
                    local_paths.append(dest_path)
                else:
                    errors.append({"url": img_url})

            # escreve de volta no dict do post
            post["image_urls"] = img_urls
            post["local_images"] = local_paths
            post["media_dir"] = post_dir
            if errors:
                post["download_errors"] = errors  # ajuda debugar

            enriched.append(post)

        return enriched

    def save_raw_data(self, data: Dict[str, Any], output_dir: str) -> str:
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        job_type = data["job_type"]
        filename = f"{job_type}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Dados salvos em: {filepath}")
        return filepath


def load_groups_config(config_path: str = "config/groups.json") -> List[str]:
    """
    Carrega configuração dos grupos do Facebook
    
    Args:
        config_path: Caminho para o arquivo de configuração
        
    Returns:
        Lista de URLs dos grupos ativos
    """
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return [
        group["url"] 
        for group in config["groups"] 
        if group.get("active", True)
    ]
