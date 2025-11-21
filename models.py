"""
Modelos Pydantic para validação de dados
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CandidateRankingRequest(BaseModel):
    """Request para rankeamento de candidatos"""
    job_id: int
    limit: Optional[int] = Field(default=10, ge=1, le=100)
    min_compatibility: Optional[float] = Field(default=0.0, ge=0.0, le=100.0)


class CandidateRankingResponse(BaseModel):
    """Response do rankeamento de candidatos"""
    candidate_id: int
    candidate_name: str
    candidate_email: str
    compatibility_score: float
    cultural_fit_score: float
    professional_fit_score: float
    ai_analysis: str
    red_flags: List[str]
    recommendation: str  # APROVADO, REPROVADO, EM_ANALISE


class TalentPoolSearchRequest(BaseModel):
    """Request para busca no banco de talentos"""
    query: str = Field(..., min_length=3, description="Busca por nome, skills, ou descrição")
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = Field(default=20, ge=1, le=100)


class TalentPoolCandidate(BaseModel):
    """Candidato do banco de talentos"""
    candidate_id: int
    name: str
    email: str
    skills: List[str]
    last_interaction: Optional[datetime]
    saved_at: Optional[datetime]
    ai_summary: Optional[str]


class CommentRequest(BaseModel):
    """Request para adicionar comentário"""
    comment: str = Field(..., min_length=1, max_length=2000)
    tags: Optional[List[str]] = None


class CommentResponse(BaseModel):
    """Response de comentário"""
    comment_id: int
    candidate_id: int
    comment: str
    tags: List[str]
    created_at: datetime
    created_by: str


class ScheduleMeetingRequest(BaseModel):
    """Request para agendar reunião"""
    candidate_email: EmailStr
    candidate_name: str
    meeting_date: str = Field(..., description="Data no formato YYYY-MM-DD")
    meeting_time: str = Field(..., description="Hora no formato HH:MM")
    meeting_type: str = Field(default="online", description="online ou presencial")
    meeting_link: Optional[str] = None
    notes: Optional[str] = None


class ScheduleMeetingResponse(BaseModel):
    """Response do agendamento"""
    success: bool
    message: str
    meeting_id: Optional[int] = None


class AIAnalysisRequest(BaseModel):
    """Request para análise de IA"""
    candidate_id: int
    job_id: int


class AIAnalysisResponse(BaseModel):
    """Response da análise de IA"""
    candidate_id: int
    job_id: int
    compatibility_score: float
    cultural_fit_score: float
    professional_fit_score: float
    ai_analysis: str
    red_flags: List[str]
    strengths: List[str]
    recommendation: str
    suggested_questions: List[str]


# Modelos para cadastro de usuários
class UserCreateRequest(BaseModel):
    """Request para criar usuário"""
    nome: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    role: str = Field(..., pattern="^(candidate|employee)$")
    senha_hash: Optional[str] = None
    cpf: Optional[str] = Field(None, pattern="^[0-9]{3}\\.[0-9]{3}\\.[0-9]{3}-[0-9]{2}$|^[0-9]{11}$")
    telefone: Optional[str] = None
    data_nascimento: Optional[str] = Field(None, description="Formato YYYY-MM-DD")
    linkedin_url: Optional[str] = None


class UserResponse(BaseModel):
    """Response de usuário"""
    id: int
    nome: str
    email: str
    role: str
    telefone: Optional[str]
    data_nascimento: Optional[datetime]
    linkedin_url: Optional[str]
    created_at: Optional[datetime]


# Modelos para cadastro de vagas
class JobCreateRequest(BaseModel):
    """Request para criar vaga"""
    titulo: str = Field(..., min_length=1, max_length=200)
    descricao: Optional[str] = None
    salario: Optional[float] = Field(None, ge=0)
    localizacao: Optional[str] = None
    tipo_contrato: Optional[str] = None
    nivel: Optional[str] = Field(None, pattern="^(Junior|Pleno|Senior)$")
    modelo_trabalho: Optional[str] = Field(None, pattern="^(Remoto|Hibrido|Presencial)$")
    departamento: Optional[str] = None


class JobResponse(BaseModel):
    """Response de vaga"""
    id: int
    titulo: str
    descricao: Optional[str]
    salario: Optional[float]
    localizacao: Optional[str]
    tipo_contrato: Optional[str]
    nivel: Optional[str]
    modelo_trabalho: Optional[str]
    departamento: Optional[str]
    created_at: Optional[datetime]
    required_skills: List[str] = []


# Modelos para skills
class SkillResponse(BaseModel):
    """Response de skill"""
    id: int
    codigo: str
    nome: str
    categoria: Optional[str]
    descricao: Optional[str]


class AddSkillToCandidateRequest(BaseModel):
    """Request para adicionar skill a candidato"""
    skill_id: int
    nivel_proficiencia: Optional[float] = Field(None, ge=0.0, le=1.0)


class AddSkillToJobRequest(BaseModel):
    """Request para adicionar skill a vaga"""
    skill_id: int
    obrigatoria: bool = Field(default=True)


class CandidateProfileResponse(BaseModel):
    """Response do perfil do candidato em JSON"""
    profile: Dict[str, Any]


class CompatibilityResponse(BaseModel):
    """Response de compatibilidade"""
    compatibility: Dict[str, Any]

