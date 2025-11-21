"""
Serviço de integração com OpenAI GPT para análise de candidatos
"""
from openai import OpenAI
from typing import Dict, List, Any
from config import settings
import logging
import json

logger = logging.getLogger(__name__)


class AIService:
    """Serviço para análise de candidatos usando OpenAI GPT"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    async def analyze_candidate_compatibility(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
        company_culture: str = ""
    ) -> Dict[str, Any]:
        """
        Analisa compatibilidade entre candidato e vaga usando GPT
        
        Args:
            candidate_data: Dados do candidato (nome, skills, perfil, etc)
            job_data: Dados da vaga (título, descrição, skills requeridas)
            company_culture: Descrição da cultura da empresa
        
        Returns:
            Dict com análise completa de compatibilidade
        """
        try:
            # Montar prompt para análise
            prompt = self._build_analysis_prompt(candidate_data, job_data, company_culture)
            
            # Chamar GPT-4 ou GPT-3.5-turbo
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",  # ou "gpt-3.5-turbo" para economia
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um especialista em RH e recrutamento com foco em compatibilidade cultural e profissional. Analise candidatos de forma objetiva e construtiva."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Processar resposta
            analysis_text = response.choices[0].message.content
            
            # Extrair informações estruturadas da resposta
            analysis = self._parse_analysis_response(analysis_text, candidate_data, job_data)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro ao analisar candidato com IA: {e}")
            # Retornar análise básica em caso de erro
            return self._get_fallback_analysis(candidate_data, job_data)
    
    def _build_analysis_prompt(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
        company_culture: str
    ) -> str:
        """Constrói o prompt para análise de compatibilidade"""
        
        candidate_skills = ", ".join(candidate_data.get("skills", []))
        job_skills = ", ".join(job_data.get("required_skills", []))
        
        prompt = f"""
Analise a compatibilidade entre o candidato e a vaga de emprego.

DADOS DO CANDIDATO:
- Nome: {candidate_data.get('name', 'N/A')}
- Skills: {candidate_skills}
- Perfil: {candidate_data.get('profile', 'Não informado')}
- Experiência: {candidate_data.get('experience', 'Não informado')}

DADOS DA VAGA:
- Título: {job_data.get('title', 'N/A')}
- Descrição: {job_data.get('description', 'N/A')}
- Skills Requeridas: {job_skills}
- Nível: {job_data.get('level', 'N/A')}

CULTURA DA EMPRESA:
{company_culture if company_culture else 'Não especificada'}

TAREFA:
Analise a compatibilidade e forneça uma resposta estruturada em JSON com:
1. compatibility_score: Score de compatibilidade geral (0-100)
2. cultural_fit_score: Score de fit cultural (0-100)
3. professional_fit_score: Score de fit profissional baseado em skills (0-100)
4. analysis: Análise detalhada em texto (2-3 parágrafos)
5. red_flags: Lista de pontos de atenção ou incompatibilidades (array de strings)
6. strengths: Lista de pontos fortes do candidato (array de strings)
7. recommendation: Recomendação (APROVADO, REPROVADO, EM_ANALISE)
8. suggested_questions: 3-5 perguntas sugeridas para entrevista (array de strings)

Responda APENAS com JSON válido, sem texto adicional.
"""
        return prompt
    
    def _parse_analysis_response(
        self,
        response_text: str,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extrai informações estruturadas da resposta do GPT"""
        try:
            # Tentar extrair JSON da resposta
            # O GPT pode retornar JSON dentro de markdown code blocks
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            analysis = json.loads(response_text)
            
            # Validar e garantir tipos corretos
            return {
                "compatibility_score": float(analysis.get("compatibility_score", 0)),
                "cultural_fit_score": float(analysis.get("cultural_fit_score", 0)),
                "professional_fit_score": float(analysis.get("professional_fit_score", 0)),
                "ai_analysis": analysis.get("analysis", ""),
                "red_flags": analysis.get("red_flags", []),
                "strengths": analysis.get("strengths", []),
                "recommendation": analysis.get("recommendation", "EM_ANALISE"),
                "suggested_questions": analysis.get("suggested_questions", [])
            }
        except json.JSONDecodeError:
            # Se não conseguir parsear JSON, extrair informações manualmente
            logger.warning("Não foi possível parsear JSON da resposta do GPT, usando fallback")
            return self._extract_info_from_text(response_text, candidate_data, job_data)
    
    def _extract_info_from_text(
        self,
        text: str,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extrai informações da resposta em texto livre"""
        # Análise básica baseada em skills
        candidate_skills = set(candidate_data.get("skills", []))
        job_skills = set(job_data.get("required_skills", []))
        
        common_skills = candidate_skills.intersection(job_skills)
        professional_score = (len(common_skills) / len(job_skills) * 100) if job_skills else 0
        
        return {
            "compatibility_score": professional_score * 0.7,  # Estimativa
            "cultural_fit_score": 50.0,  # Padrão
            "professional_fit_score": professional_score,
            "ai_analysis": text[:500],  # Primeiros 500 caracteres
            "red_flags": [],
            "strengths": list(common_skills),
            "recommendation": "EM_ANALISE",
            "suggested_questions": []
        }
    
    def _get_fallback_analysis(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Retorna análise básica quando a IA falha"""
        candidate_skills = set(candidate_data.get("skills", []))
        job_skills = set(job_data.get("required_skills", []))
        
        common_skills = candidate_skills.intersection(job_skills)
        professional_score = (len(common_skills) / len(job_skills) * 100) if job_skills else 0
        
        return {
            "compatibility_score": professional_score * 0.7,
            "cultural_fit_score": 50.0,
            "professional_fit_score": professional_score,
            "ai_analysis": "Análise automática baseada em skills. Análise detalhada temporariamente indisponível.",
            "red_flags": [],
            "strengths": list(common_skills),
            "recommendation": "EM_ANALISE",
            "suggested_questions": []
        }
    
    async def search_talent_pool(
        self,
        query: str,
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Busca inteligente no banco de talentos usando GPT para entender intenção
        
        Args:
            query: Texto de busca (ex: "desenvolvedor Python sênior")
            candidates: Lista de candidatos do banco
        
        Returns:
            Lista de candidatos relevantes ordenados por relevância
        """
        try:
            # Usar GPT para entender a intenção da busca
            prompt = f"""
Analise a seguinte busca e identifique os critérios principais:
"{query}"

Extraia:
1. Skills ou tecnologias mencionadas
2. Nível de experiência (júnior, pleno, sênior)
3. Área ou função
4. Outros requisitos

Responda em JSON:
{{
    "skills": ["skill1", "skill2"],
    "level": "júnior|pleno|sênior|qualquer",
    "area": "área mencionada ou null",
    "other_requirements": ["req1", "req2"]
}}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um assistente que extrai critérios de busca de vagas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            search_criteria = json.loads(response.choices[0].message.content)
            
            # Filtrar e rankear candidatos baseado nos critérios
            ranked_candidates = self._rank_candidates_by_criteria(candidates, search_criteria)
            
            return ranked_candidates
            
        except Exception as e:
            logger.error(f"Erro na busca inteligente: {e}")
            # Fallback: busca simples por texto
            return self._simple_text_search(candidates, query)
    
    def _rank_candidates_by_criteria(
        self,
        candidates: List[Dict[str, Any]],
        criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Rankeia candidatos baseado nos critérios extraídos"""
        scored_candidates = []
        
        for candidate in candidates:
            score = 0.0
            candidate_skills = [s.lower() for s in candidate.get("skills", [])]
            
            # Score por skills
            required_skills = [s.lower() for s in criteria.get("skills", [])]
            matching_skills = set(candidate_skills).intersection(set(required_skills))
            if required_skills:
                score += (len(matching_skills) / len(required_skills)) * 50
            
            # Score por nível (se especificado)
            candidate_level = candidate.get("level", "").lower()
            required_level = criteria.get("level", "").lower()
            if required_level and required_level != "qualquer":
                if required_level in candidate_level or candidate_level in required_level:
                    score += 30
            
            # Score por área
            candidate_area = candidate.get("area", "").lower()
            required_area = criteria.get("area", "").lower()
            if required_area and required_area in candidate_area:
                score += 20
            
            scored_candidates.append({
                **candidate,
                "relevance_score": score
            })
        
        # Ordenar por score
        scored_candidates.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_candidates
    
    def _simple_text_search(
        self,
        candidates: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """Busca simples por texto"""
        query_lower = query.lower()
        scored = []
        
        for candidate in candidates:
            score = 0.0
            name = candidate.get("name", "").lower()
            skills = " ".join([s.lower() for s in candidate.get("skills", [])])
            profile = candidate.get("profile", "").lower()
            
            text = f"{name} {skills} {profile}"
            
            if query_lower in text:
                score = 100.0
            else:
                # Score parcial por palavras em comum
                query_words = set(query_lower.split())
                text_words = set(text.split())
                common = query_words.intersection(text_words)
                if query_words:
                    score = (len(common) / len(query_words)) * 100
            
            scored.append({**candidate, "relevance_score": score})
        
        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return [c for c in scored if c["relevance_score"] > 0]


# Instância global do serviço de IA
ai_service = AIService()

