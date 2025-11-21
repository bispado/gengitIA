"""
API REST para Sistema de RH com IA Generativa
Sistema de Recrutamento Inteligente com rankeamento, banco de talentos e análise de IA
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import List, Optional
import json
import os

from config import settings
from database import db
from models import (
    CandidateRankingRequest,
    CandidateRankingResponse,
    TalentPoolSearchRequest,
    TalentPoolCandidate,
    CommentRequest,
    CommentResponse,
    ScheduleMeetingRequest,
    ScheduleMeetingResponse,
    AIAnalysisRequest,
    AIAnalysisResponse,
    UserCreateRequest,
    UserResponse,
    JobCreateRequest,
    JobResponse,
    SkillResponse,
    AddSkillToCandidateRequest,
    AddSkillToJobRequest,
    CandidateProfileResponse,
    CompatibilityResponse
)
from services.ai_service import ai_service
from services.database_service import db_service
from services.email_service import email_service

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação"""
    # Startup
    logger.info("Iniciando aplicação...")
    try:
        db.create_pool()
        logger.info("Aplicação iniciada com sucesso")
    except Exception as e:
        logger.error(f"Erro ao iniciar aplicação: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Encerrando aplicação...")
    db.close_pool()
    logger.info("Aplicação encerrada")


# Criar aplicação FastAPI
app = FastAPI(
    title="Sistema de RH com IA Generativa",
    description="API para recrutamento inteligente com rankeamento de candidatos, banco de talentos e análise de IA",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "Sistema de RH com IA Generativa",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy"}


@app.post("/api/candidates/ranking", response_model=List[CandidateRankingResponse])
async def rank_candidates(request: CandidateRankingRequest):
    """
    Rankeia candidatos para uma vaga usando IA
    
    Analisa todos os candidatos e retorna ranking ordenado por compatibilidade,
    incluindo análise de IA generativa.
    """
    try:
        # Buscar dados da vaga
        job_data = await db_service.get_job_data(request.job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")
        
        # Buscar todos os candidatos
        all_candidates = await db_service.get_all_candidates()
        
        if not all_candidates:
            return []
        
        # Analisar cada candidato com IA
        ranked_candidates = []
        
        for candidate in all_candidates:
            try:
                # Buscar dados completos do candidato
                candidate_data = await db_service.get_candidate_data(candidate["id"])
                if not candidate_data:
                    continue
                
                # Analisar com IA
                analysis = await ai_service.analyze_candidate_compatibility(
                    candidate_data=candidate_data,
                    job_data=job_data,
                    company_culture=""  # Pode ser expandido no futuro
                )
                
                # Filtrar por score mínimo
                if analysis["compatibility_score"] < request.min_compatibility:
                    continue
                
                # Salvar resultado no banco
                await db_service.save_model_result(
                    candidate_id=candidate["id"],
                    job_id=request.job_id,
                    compatibility_score=analysis["compatibility_score"],
                    cultural_fit_score=analysis["cultural_fit_score"],
                    professional_fit_score=analysis["professional_fit_score"],
                    ai_analysis=analysis["ai_analysis"],
                    red_flags=analysis["red_flags"],
                    recommendation=analysis["recommendation"]
                )
                
                ranked_candidates.append({
                    "candidate_id": candidate["id"],
                    "candidate_name": candidate_data["name"],
                    "candidate_email": candidate_data["email"],
                    "compatibility_score": analysis["compatibility_score"],
                    "cultural_fit_score": analysis["cultural_fit_score"],
                    "professional_fit_score": analysis["professional_fit_score"],
                    "ai_analysis": analysis["ai_analysis"],
                    "red_flags": analysis["red_flags"],
                    "recommendation": analysis["recommendation"]
                })
                
            except Exception as e:
                logger.error(f"Erro ao analisar candidato {candidate['id']}: {e}")
                continue
        
        # Ordenar por score de compatibilidade
        ranked_candidates.sort(key=lambda x: x["compatibility_score"], reverse=True)
        
        # Limitar resultados
        return ranked_candidates[:request.limit]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no rankeamento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.post("/api/talent-pool/search", response_model=List[TalentPoolCandidate])
async def search_talent_pool(request: TalentPoolSearchRequest):
    """
    Busca inteligente no banco de talentos usando IA
    
    Permite busca por texto livre que é interpretada pela IA para encontrar
    candidatos relevantes.
    """
    try:
        # Buscar todos os candidatos
        all_candidates = await db_service.get_all_candidates()
        
        if not all_candidates:
            return []
        
        # Preparar dados para busca com IA
        candidates_data = []
        for candidate in all_candidates:
            candidate_full = await db_service.get_candidate_data(candidate["id"])
            if candidate_full:
                candidates_data.append({
                    "id": candidate_full["id"],
                    "name": candidate_full["name"],
                    "email": candidate_full["email"],
                    "skills": candidate_full["skills"],
                    "profile": candidate_full.get("profile", ""),
                    "level": ""  # Pode ser expandido
                })
        
        # Buscar com IA
        ranked_results = await ai_service.search_talent_pool(
            query=request.query,
            candidates=candidates_data
        )
        
        # Formatar resposta
        results = []
        for candidate in ranked_results[:request.limit]:
            results.append({
                "candidate_id": candidate["id"],
                "name": candidate["name"],
                "email": candidate["email"],
                "skills": candidate["skills"],
                "last_interaction": None,  # Pode ser expandido
                "saved_at": None,  # Pode ser expandido
                "ai_summary": f"Relevância: {candidate.get('relevance_score', 0):.1f}%"
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Erro na busca de talentos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.post("/api/candidates/{candidate_id}/comments", response_model=CommentResponse)
async def add_comment(candidate_id: int, request: CommentRequest):
    """
    Adiciona comentário a um candidato salvo no banco de talentos
    """
    try:
        # Verificar se candidato existe
        candidate = await db_service.get_candidate_data(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidato não encontrado")
        
        # Salvar comentário
        comment_id = await db_service.save_comment(
            candidate_id=candidate_id,
            comment=request.comment,
            tags=request.tags
        )
        
        if not comment_id:
            raise HTTPException(status_code=500, detail="Erro ao salvar comentário")
        
        # Buscar comentário salvo
        comments = await db_service.get_candidate_comments(candidate_id)
        saved_comment = next((c for c in comments if c["id"] == comment_id), None)
        
        if not saved_comment:
            raise HTTPException(status_code=500, detail="Comentário não encontrado após salvar")
        
        return CommentResponse(
            comment_id=saved_comment["id"],
            candidate_id=candidate_id,
            comment=saved_comment["comment"],
            tags=saved_comment["tags"],
            created_at=saved_comment["created_at"],
            created_by=saved_comment["created_by"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao adicionar comentário: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.get("/api/candidates/{candidate_id}/comments", response_model=List[CommentResponse])
async def get_comments(candidate_id: int):
    """Busca comentários de um candidato"""
    try:
        comments = await db_service.get_candidate_comments(candidate_id)
        
        return [
            CommentResponse(
                comment_id=c["id"],
                candidate_id=candidate_id,
                comment=c["comment"],
                tags=c["tags"],
                created_at=c["created_at"],
                created_by=c["created_by"]
            )
            for c in comments
        ]
        
    except Exception as e:
        logger.error(f"Erro ao buscar comentários: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.post("/api/meetings/schedule", response_model=ScheduleMeetingResponse)
async def schedule_meeting(request: ScheduleMeetingRequest):
    """
    Agenda reunião com candidato e envia email de convite
    """
    try:
        # Enviar email
        success = await email_service.send_meeting_invitation(
            candidate_email=request.candidate_email,
            candidate_name=request.candidate_name,
            meeting_date=request.meeting_date,
            meeting_time=request.meeting_time,
            meeting_type=request.meeting_type,
            meeting_link=request.meeting_link,
            notes=request.notes
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Erro ao enviar email")
        
        return ScheduleMeetingResponse(
            success=True,
            message=f"Email de convite enviado com sucesso para {request.candidate_email}",
            meeting_id=None  # Pode ser expandido para salvar no banco
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao agendar reunião: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.post("/api/ai/analyze", response_model=AIAnalysisResponse)
async def analyze_candidate(request: AIAnalysisRequest):
    """
    Análise detalhada de compatibilidade entre candidato e vaga usando IA
    """
    try:
        # Buscar dados
        candidate_data = await db_service.get_candidate_data(request.candidate_id)
        if not candidate_data:
            raise HTTPException(status_code=404, detail="Candidato não encontrado")
        
        job_data = await db_service.get_job_data(request.job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")
        
        # Analisar com IA
        analysis = await ai_service.analyze_candidate_compatibility(
            candidate_data=candidate_data,
            job_data=job_data,
            company_culture=""
        )
        
        # Salvar resultado
        await db_service.save_model_result(
            candidate_id=request.candidate_id,
            job_id=request.job_id,
            compatibility_score=analysis["compatibility_score"],
            cultural_fit_score=analysis["cultural_fit_score"],
            professional_fit_score=analysis["professional_fit_score"],
            ai_analysis=analysis["ai_analysis"],
            red_flags=analysis["red_flags"],
            recommendation=analysis["recommendation"]
        )
        
        return AIAnalysisResponse(
            candidate_id=request.candidate_id,
            job_id=request.job_id,
            compatibility_score=analysis["compatibility_score"],
            cultural_fit_score=analysis["cultural_fit_score"],
            professional_fit_score=analysis["professional_fit_score"],
            ai_analysis=analysis["ai_analysis"],
            red_flags=analysis["red_flags"],
            strengths=analysis.get("strengths", []),
            recommendation=analysis["recommendation"],
            suggested_questions=analysis.get("suggested_questions", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na análise de IA: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ==================== ENDPOINTS DE CADASTRO E GERENCIAMENTO ====================

@app.post("/api/users", response_model=UserResponse, status_code=201)
async def create_user(request: UserCreateRequest):
    """
    Cria um novo usuário (candidato ou funcionário)
    
    Usa a procedure PRC_INSERT_USER do banco de dados.
    """
    try:
        user_id = await db_service.create_user(
            nome=request.nome,
            email=request.email,
            role=request.role,
            senha_hash=request.senha_hash,
            cpf=request.cpf,
            telefone=request.telefone,
            data_nascimento=request.data_nascimento,
            linkedin_url=request.linkedin_url
        )
        
        if not user_id:
            raise HTTPException(status_code=400, detail="Erro ao criar usuário")
        
        # Buscar usuário criado
        user = await db_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado após criação")
        
        return UserResponse(**user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.get("/api/users", response_model=List[UserResponse])
async def list_users(role: Optional[str] = None):
    """
    Lista todos os usuários
    
    Pode ser filtrado por role (candidate ou employee).
    """
    try:
        users = await db_service.list_users(role=role)
        return [UserResponse(**user) for user in users]
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Busca um usuário por ID"""
    try:
        user = await db_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        return UserResponse(**user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar usuário: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.post("/api/jobs", response_model=JobResponse, status_code=201)
async def create_job(request: JobCreateRequest):
    """
    Cria uma nova vaga de emprego
    
    Usa a procedure PRC_INSERT_JOB do banco de dados.
    """
    try:
        job_id = await db_service.create_job(
            titulo=request.titulo,
            descricao=request.descricao,
            salario=request.salario,
            localizacao=request.localizacao,
            tipo_contrato=request.tipo_contrato,
            nivel=request.nivel,
            modelo_trabalho=request.modelo_trabalho,
            departamento=request.departamento
        )
        
        if not job_id:
            raise HTTPException(status_code=400, detail="Erro ao criar vaga")
        
        # Buscar vaga criada
        job = await db_service.get_job_data(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada após criação")
        
        return JobResponse(
            id=job["id"],
            titulo=job["title"],
            descricao=job["description"],
            salario=job["salary"],
            localizacao=job["location"],
            tipo_contrato=job["contract_type"],
            nivel=job["level"],
            modelo_trabalho=job["work_model"],
            departamento=job["department"],
            created_at=None,
            required_skills=job["required_skills"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar vaga: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.get("/api/jobs", response_model=List[JobResponse])
async def list_jobs():
    """Lista todas as vagas"""
    try:
        jobs = await db_service.list_jobs()
        return [JobResponse(**job) for job in jobs]
    except Exception as e:
        logger.error(f"Erro ao listar vagas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int):
    """Busca uma vaga por ID"""
    try:
        job = await db_service.get_job_data(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")
        
        return JobResponse(
            id=job["id"],
            titulo=job["title"],
            descricao=job["description"],
            salario=job["salary"],
            localizacao=job["location"],
            tipo_contrato=job["contract_type"],
            nivel=job["level"],
            modelo_trabalho=job["work_model"],
            departamento=job["department"],
            created_at=None,
            required_skills=job["required_skills"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar vaga: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.get("/api/skills", response_model=List[SkillResponse])
async def list_skills():
    """Lista todas as skills disponíveis"""
    try:
        skills = await db_service.list_skills()
        return [SkillResponse(**skill) for skill in skills]
    except Exception as e:
        logger.error(f"Erro ao listar skills: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.post("/api/candidates/{candidate_id}/skills", status_code=201)
async def add_skill_to_candidate(candidate_id: int, request: AddSkillToCandidateRequest):
    """
    Adiciona uma skill a um candidato
    
    Usa a procedure PRC_INSERT_CANDIDATE_SKILL do banco de dados.
    """
    try:
        # Verificar se candidato existe
        candidate = await db_service.get_candidate_data(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidato não encontrado")
        
        candidate_skill_id = await db_service.add_skill_to_candidate(
            user_id=candidate_id,
            skill_id=request.skill_id,
            nivel_proficiencia=request.nivel_proficiencia
        )
        
        if not candidate_skill_id:
            raise HTTPException(status_code=400, detail="Erro ao adicionar skill ao candidato")
        
        return {
            "success": True,
            "candidate_skill_id": candidate_skill_id,
            "message": "Skill adicionada com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao adicionar skill: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.post("/api/jobs/{job_id}/skills", status_code=201)
async def add_skill_to_job(job_id: int, request: AddSkillToJobRequest):
    """Adiciona uma skill a uma vaga"""
    try:
        # Verificar se vaga existe
        job = await db_service.get_job_data(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")
        
        job_skill_id = await db_service.add_skill_to_job(
            job_id=job_id,
            skill_id=request.skill_id,
            obrigatoria=request.obrigatoria
        )
        
        if not job_skill_id:
            raise HTTPException(status_code=400, detail="Erro ao adicionar skill à vaga ou skill já existe")
        
        return {
            "success": True,
            "job_skill_id": job_skill_id,
            "message": "Skill adicionada à vaga com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao adicionar skill à vaga: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.get("/api/candidates/{candidate_id}/profile", response_model=CandidateProfileResponse)
async def get_candidate_profile(candidate_id: int):
    """
    Obtém perfil completo do candidato em JSON
    
    Usa a função FN_CANDIDATE_PROFILE_AS_JSON do banco de dados.
    """
    try:
        profile_json = await db_service.get_candidate_profile_json(candidate_id)
        
        if not profile_json:
            raise HTTPException(status_code=404, detail="Perfil do candidato não encontrado")
        
        import json
        profile = json.loads(profile_json)
        
        return CandidateProfileResponse(profile=profile)
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Erro ao processar perfil JSON")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar perfil: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.get("/api/compatibility/{candidate_id}/{job_id}", response_model=CompatibilityResponse)
async def get_compatibility(candidate_id: int, job_id: int):
    """
    Calcula compatibilidade entre candidato e vaga
    
    Usa a função FN_CALC_COMPATIBILITY do banco de dados.
    """
    try:
        compatibility_json = await db_service.calculate_compatibility(candidate_id, job_id)
        
        if not compatibility_json:
            raise HTTPException(status_code=404, detail="Não foi possível calcular compatibilidade")
        
        import json
        compatibility = json.loads(compatibility_json)
        
        return CompatibilityResponse(compatibility=compatibility)
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Erro ao processar JSON de compatibilidade")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao calcular compatibilidade: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.get("/api/candidates/{candidate_id}/model-results")
async def get_candidate_model_results(candidate_id: int):
    """Lista todos os resultados de análise de IA para um candidato"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                mr.id,
                mr.job_id,
                j.titulo AS job_titulo,
                mr.score_afinidade_cultural,
                mr.score_compatibilidade_profissional,
                mr.red_flags,
                mr.recomendacao,
                mr.detalhes,
                mr.created_at
            FROM MODEL_RESULTS mr
            INNER JOIN JOBS j ON mr.job_id = j.id
            WHERE mr.user_id = :candidate_id
            ORDER BY mr.created_at DESC
        """, candidate_id=candidate_id)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "job_id": row[1],
                "job_titulo": row[2],
                "score_afinidade_cultural": row[3],
                "score_compatibilidade_profissional": row[4],
                "red_flags": row[5],
                "recomendacao": row[6],
                "detalhes": row[7],
                "created_at": row[8]
            })
        
        cursor.close()
        db.pool.release(conn)
        
        return results
        
    except Exception as e:
        logger.error(f"Erro ao buscar resultados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    # Na Azure, use a variável PORT do ambiente
    port = int(os.getenv("PORT", settings.api_port))
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=port,
        reload=settings.api_debug
    )

