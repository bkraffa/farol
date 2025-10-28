"""
Calculador de score de potencial de revenda
Analisa múltiplos fatores para determinar se um equipamento vale a pena revender
"""
from typing import Dict, Any, List
import re


class ResaleScorer:
    """Calcula score de potencial de revenda"""
    
    # Marcas populares (maior demanda)
    TOP_BRANDS = {
    # Tier S (25 pontos) - Marcas premium/líderes absolutas
    'duotone': 25,
    'mystic': 25,
    
    # Tier A (22-24 pontos) - Marcas top
    'north': 24,
    'core': 23,
    'manera': 23,
    'ion': 23,
    "liewe": 22,
    
    # Tier B (20-21 pontos) - Marcas fortes
    'cabrinha': 21,
    'prolimit': 20,
    'slingshot': 20,
    'ride engine': 20,
    
    # Tier C (17-19 pontos) - Marcas consolidadas
    'reedin': 18,
    "crazy fly": 19,
    'ozone': 18,
    'dakine': 18,
    'rip curl': 19,
    'oneill': 19,
    'shinn': 18,
    'patagonia': 18,
    'naish': 17,
    'f-one': 17,

    
    # Tier D (14-16 pontos) - Marcas boas/intermediárias
    "eleveight": 16,
    'airush': 15,
    'liquid force': 16,
    'crazyfly': 16,
    'billabong': 16,
    'nobile': 15,
    'appletree': 15,
    'eleveight': 15,
    'flysurfer': 14,
    'brunotti': 14,
    
    # Tier E (12-13 pontos) - Marcas básicas/antigas
    'carved': 13,
    'gaastra': 12,
    'best': 12,
    'hurley': 12,
    'roxy': 12,
    'quiksilver': 12,
    'rrd': 12
}
    
    # Condições (quanto melhor, mais vale)
    CONDITION_SCORES = {
        'novo': 25,
        'seminovo': 22,
        'bom_estado': 18,
        'usado': 12,
        'precisa_reparo': 5,
        'desconhecido': 12
    }
    
    # Palavras que indicam interesse nos comentários
    INTEREST_KEYWORDS = [
        'quanto', 'preço', 'valor', 'comprar', 'compro',
        'interessado', 'interesse', 'disponível', 'vendo',
        'aceita', 'troca', 'pago', 'whatsapp', 'zap',
        'reservado', 'vendido', 'sold', 'dm', 'direct', 'inbox' , 'chamei'  ]
    
    # Palavras que indicam desinteresse
    DISINTEREST_KEYWORDS = [
        'caro', 'carão', 'absurdo', 'exagerado',
        'não vale', 'zuado', 'ruim', 'péssimo', 'lixo',
    ]
    
    @classmethod
    def calculate_score(
        cls,
        equipment_type: str,
        brand: str,
        year: int,
        price: float,
        condition: str,
        has_repair: bool,
        comments: List[str],
        comments_count: int,
        likes_count: int
    ) -> Dict[str, Any]:
        """
        Calcula score de potencial de revenda (0-100)
        
        Args:
            equipment_type: Tipo do equipamento
            brand: Marca
            year: Ano
            price: Preço
            condition: Condição
            has_repair: Tem reparo?
            comments: Lista de comentários
            comments_count: Total de comentários
            likes_count: Total de likes
            
        Returns:
            Dict com score total e breakdown
        """
        scores = {}
        
        # 1. SCORE DE MARCA (0-25 pontos)
        scores['brand_score'] = cls._score_brand(brand)
        
        # 2. SCORE DE PREÇO (0-25 pontos)
        scores['price_score'] = cls._score_price(
            equipment_type, brand, year, price, has_repair
        )
        
        # 3. SCORE DE CONDIÇÃO (0-25 pontos)
        scores['condition_score'] = cls._score_condition(condition, has_repair)
        
        # 4. SCORE DE INTERESSE (0-25 pontos)
        scores['interest_score'] = cls._score_interest(
            comments, comments_count, likes_count
        )
        
        # SCORE TOTAL
        total_score = sum(scores.values())
        
        # CLASSIFICAÇÃO
        classification = cls._classify_score(total_score)
        
        # RECOMENDAÇÃO
        recommendation = cls._generate_recommendation(
            total_score, scores, price, brand, condition
        )
        
        return {
            'total_score': round(total_score, 1),
            'classification': classification,
            'factors': scores,
            'recommendation': recommendation,
            'breakdown': cls._generate_breakdown(scores)
        }
    
    @classmethod
    def _score_brand(cls, brand: str) -> float:
        """Score baseado na marca (0-25)"""
        if not brand:
            return 10.0
        
        brand_lower = brand.lower()
        
        # Buscar marca exata
        if brand_lower in cls.TOP_BRANDS:
            return cls.TOP_BRANDS[brand_lower]
        
        # Buscar marca parcial
        for top_brand, score in cls.TOP_BRANDS.items():
            if top_brand in brand_lower or brand_lower in top_brand:
                return score * 0.9  # 10% de desconto por match parcial
        
        # Marca desconhecida
        return 8.0
    
    @classmethod
    def _score_price(
        cls,
        equipment_type: str,
        brand: str,
        year: int,
        price: float,
        has_repair: bool
    ) -> float:
        """Score baseado no preço vs valor de mercado (0-25)"""
        if not price:
            return 10.0  # Sem preço, score neutro
        
        # Preços médios de referência (2024)
        reference_prices = {
            'kite': {
                'new': 8000,
                'used': 4000,
                'with_repair': 2500
            },
            'board': {
                'new': 3500,
                'used': 1800,
                'with_repair': 1200
            },
            'bar': {
                'new': 2500,
                'used': 1200,
                'with_repair': 800
            }
        }
        
        # Pegar preço de referência
        ref_prices = reference_prices.get(equipment_type, reference_prices['kite'])
        
        if has_repair:
            ref_price = ref_prices['with_repair']
        elif year and year >= 2022:
            ref_price = ref_prices['new'] * 0.7  # 30% de depreciação
        else:
            ref_price = ref_prices['used']
        
        # Calcular quanto abaixo/acima do preço de referência
        price_ratio = price / ref_price
        
        if price_ratio <= 0.5:  # 50% abaixo = excelente
            return 25.0
        elif price_ratio <= 0.7:  # 30% abaixo = ótimo
            return 22.0
        elif price_ratio <= 0.9:  # 10% abaixo = bom
            return 18.0
        elif price_ratio <= 1.1:  # preço justo
            return 15.0
        elif price_ratio <= 1.3:  # 30% acima = aceitável
            return 10.0
        else:  # muito caro
            return 5.0
    
    @classmethod
    def _score_condition(cls, condition: str, has_repair: bool) -> float:
        """Score baseado na condição (0-25)"""
        base_score = cls.CONDITION_SCORES.get(condition, 10.0)
        
        # Penalidade por reparo
        if has_repair:
            base_score *= 0.5
        
        return base_score
    
    @classmethod
    def _score_interest(
        cls,
        comments: List[str],
        comments_count: int,
        likes_count: int
    ) -> float:
        """Score baseado no interesse demonstrado (0-25)"""
        score = 0.0
        
        # 1. Quantidade de engajamento (0-10 pontos)
        total_engagement = comments_count + (likes_count * 0.5)
        if total_engagement >= 20:
            score += 10
        elif total_engagement >= 10:
            score += 7
        elif total_engagement >= 5:
            score += 5
        elif total_engagement >= 2:
            score += 3
        
        # 2. Análise de comentários (0-15 pontos)
        if comments:
            interest_count = 0
            disinterest_count = 0
            
            for comment in comments:
                comment_lower = comment.lower()
                
                # Contar palavras de interesse
                for keyword in cls.INTEREST_KEYWORDS:
                    if keyword in comment_lower:
                        interest_count += 1
                        break
                
                # Contar palavras de desinteresse
                for keyword in cls.DISINTEREST_KEYWORDS:
                    if keyword in comment_lower:
                        disinterest_count += 1
                        break
            
            # Calcular score de interesse dos comentários
            if interest_count > disinterest_count:
                comment_score = min(15, interest_count * 3)
                score += comment_score
            elif disinterest_count > 0:
                score += max(0, 5 - disinterest_count * 2)
            else:
                score += 5  # Comentários neutros
        
        return min(25.0, score)
    
    @classmethod
    def _classify_score(cls, score: float) -> str:
        """Classifica o score"""
        if score >= 80:
            return "⭐⭐⭐ EXCELENTE - Alta prioridade"
        elif score >= 65:
            return "⭐⭐ BOM - Vale a pena considerar"
        elif score >= 50:
            return "⭐ MÉDIO - Avaliar melhor"
        else:
            return "❌ BAIXO - Não recomendado"
    
    @classmethod
    def _generate_recommendation(
        cls,
        total_score: float,
        scores: Dict[str, float],
        price: float,
        brand: str,
        condition: str
    ) -> str:
        """Gera recomendação textual"""
        if total_score >= 80:
            return "Ótima oportunidade de revenda! Equipamento popular, bom preço e alto interesse."
        
        elif total_score >= 65:
            reasons = []
            if scores['brand_score'] >= 20:
                reasons.append("marca forte")
            if scores['price_score'] >= 20:
                reasons.append("preço competitivo")
            if scores['interest_score'] >= 20:
                reasons.append("alto interesse")
            
            if reasons:
                return f"Vale considerar pela {' e '.join(reasons)}."
            else:
                return "Oportunidade razoável de revenda."
        
        elif total_score >= 50:
            warnings = []
            if scores['price_score'] < 15:
                warnings.append("preço elevado")
            if scores['condition_score'] < 15:
                warnings.append("condição questionável")
            if scores['interest_score'] < 10:
                warnings.append("baixo interesse")
            
            if warnings:
                return f"Atenção: {' e '.join(warnings)}. Avaliar com cuidado."
            else:
                return "Oportunidade média. Analisar outros fatores."
        
        else:
            return "Não recomendado para revenda no momento."
    
    @classmethod
    def _generate_breakdown(cls, scores: Dict[str, float]) -> str:
        """Gera breakdown visual dos scores"""
        breakdown = []
        
        for factor, score in scores.items():
            factor_name = factor.replace('_score', '').title()
            bars = '█' * int(score / 5)  # 5 pontos = 1 barra
            breakdown.append(f"{factor_name}: {bars} {score:.1f}/25")
        
        return '\n'.join(breakdown)
