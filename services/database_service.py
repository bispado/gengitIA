"""
Serviço para operações no banco de dados Oracle
"""
import oracledb
from typing import List, Dict, Any, Optional
from database import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseService:
    """Serviço para operações no banco de dados"""
    
    async def get_candidate_data(self, candidate_id: int) -> Optional[Dict[str, Any]]:
        """Busca dados completos do candidato"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Buscar dados do candidato
            cursor.execute("""
                SELECT id, nome, email, role, telefone, data_nascimento, linkedin_url
                FROM USERS
                WHERE id = :candidate_id AND role = 'candidate'
            """, candidate_id=candidate_id)
            
            row = cursor.fetchone()
            if not row:
                return None
            
            candidate = {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "role": row[3],
                "phone": row[4],
                "birth_date": row[5],
                "linkedin_url": row[6],
                "skills": [],
                "profile": ""
            }
            
            # Buscar skills do candidato
            cursor.execute("""
                SELECT s.nome, cs.nivel_proficiencia
                FROM CANDIDATE_SKILLS cs
                INNER JOIN SKILLS s ON cs.skill_id = s.id
                WHERE cs.user_id = :candidate_id
                ORDER BY cs.nivel_proficiencia DESC
            """, candidate_id=candidate_id)
            
            skills = []
            for skill_row in cursor.fetchall():
                skills.append(skill_row[0])
            
            candidate["skills"] = skills
            
            cursor.close()
            db.pool.release(conn)
            
            return candidate
            
        except Exception as e:
            logger.error(f"Erro ao buscar candidato: {e}")
            if conn:
                db.pool.release(conn)
            return None
    
    async def get_job_data(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Busca dados completos da vaga"""
        conn = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Buscar dados da vaga
            cursor.execute("""
                SELECT id, titulo, descricao, salario, localizacao, tipo_contrato, 
                       nivel, modelo_trabalho, departamento
                FROM JOBS
                WHERE id = :job_id
            """, job_id=job_id)
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Converter LOB para string se necessário
            descricao = row[2]
            if descricao is not None:
                if isinstance(descricao, oracledb.LOB):
                    descricao = descricao.read()
                elif hasattr(descricao, 'read'):
                    descricao = descricao.read()
                descricao = str(descricao) if descricao else ""
            else:
                descricao = ""
            
            job = {
                "id": row[0],
                "title": row[1],
                "description": descricao,
                "salary": row[3],
                "location": row[4],
                "contract_type": row[5],
                "level": row[6] or "",
                "work_model": row[7],
                "department": row[8],
                "required_skills": []
            }
            
            # Buscar skills requeridas
            cursor.execute("""
                SELECT s.nome
                FROM JOB_SKILLS js
                INNER JOIN SKILLS s ON js.skill_id = s.id
                WHERE js.job_id = :job_id
            """, job_id=job_id)
            
            skills = [row[0] for row in cursor.fetchall()]
            job["required_skills"] = skills
            
            cursor.close()
            db.pool.release(conn)
            
            return job
            
        except Exception as e:
            logger.error(f"Erro ao buscar vaga: {e}")
            if conn:
                db.pool.release(conn)
            return None
    
    async def get_all_candidates(self) -> List[Dict[str, Any]]:
        """Busca todos os candidatos"""
        conn = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.id, u.nome, u.email, u.telefone, u.linkedin_url
                FROM USERS u
                WHERE u.role = 'candidate'
                ORDER BY u.nome
            """)
            
            candidates = []
            for row in cursor.fetchall():
                candidate = {
                    "id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "phone": row[3],
                    "linkedin_url": row[4],
                    "skills": []
                }
                
                # Buscar skills
                cursor2 = conn.cursor()
                cursor2.execute("""
                    SELECT s.nome
                    FROM CANDIDATE_SKILLS cs
                    INNER JOIN SKILLS s ON cs.skill_id = s.id
                    WHERE cs.user_id = :user_id
                """, user_id=row[0])
                
                candidate["skills"] = [r[0] for r in cursor2.fetchall()]
                cursor2.close()
                
                candidates.append(candidate)
            
            cursor.close()
            db.pool.release(conn)
            
            return candidates
            
        except Exception as e:
            logger.error(f"Erro ao buscar candidatos: {e}")
            if conn:
                db.pool.release(conn)
            return []
    
    async def save_model_result(
        self,
        candidate_id: int,
        job_id: int,
        compatibility_score: float,
        cultural_fit_score: float,
        professional_fit_score: float,
        ai_analysis: str,
        red_flags: List[str],
        recommendation: str
    ) -> Optional[int]:
        """Salva resultado da análise de IA"""
        conn = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            red_flags_text = ", ".join(red_flags) if red_flags else None
            
            result_id_var = cursor.var(oracledb.NUMBER)
            cursor.execute("""
                BEGIN
                    PRC_INSERT_MODEL_RESULT(
                        p_user_id => :user_id,
                        p_job_id => :job_id,
                        p_score_afinidade_cultural => :cultural_score,
                        p_score_compatibilidade_profissional => :professional_score,
                        p_red_flags => :red_flags,
                        p_recomendacao => :recommendation,
                        p_detalhes => :details,
                        p_model_result_id => :result_id
                    );
                END;
            """, {
                "user_id": candidate_id,
                "job_id": job_id,
                "cultural_score": cultural_fit_score,
                "professional_score": professional_fit_score,
                "red_flags": red_flags_text,
                "recommendation": recommendation,
                "details": ai_analysis,
                "result_id": result_id_var
            })
            
            result_id = result_id_var.getvalue()[0] if result_id_var.getvalue() else None
            
            conn.commit()
            cursor.close()
            db.pool.release(conn)
            
            return result_id
            
        except Exception as e:
            logger.error(f"Erro ao salvar resultado do modelo: {e}")
            if conn:
                conn.rollback()
                db.pool.release(conn)
            return None
    
    async def save_comment(
        self,
        candidate_id: int,
        comment: str,
        tags: Optional[List[str]] = None
    ) -> Optional[int]:
        """Salva comentário em candidato"""
        conn = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Criar tabela de comentários se não existir
            cursor.execute("""
                SELECT COUNT(*) FROM user_tables WHERE table_name = 'CANDIDATE_COMMENTS'
            """)
            
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    CREATE TABLE CANDIDATE_COMMENTS (
                        id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                        candidate_id NUMBER NOT NULL,
                        comment_text CLOB NOT NULL,
                        tags VARCHAR2(500),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by VARCHAR2(100) DEFAULT USER,
                        CONSTRAINT fk_comment_candidate FOREIGN KEY (candidate_id) 
                            REFERENCES USERS(id)
                    )
                """)
            
            tags_str = ", ".join(tags) if tags else None
            
            cursor.execute("""
                INSERT INTO CANDIDATE_COMMENTS (candidate_id, comment_text, tags)
                VALUES (:candidate_id, :comment, :tags)
                RETURNING id INTO :comment_id
            """, {
                "candidate_id": candidate_id,
                "comment": comment,
                "tags": tags_str,
                "comment_id": cursor.var(oracledb.NUMBER)
            })
            
            comment_id = cursor.var(oracledb.NUMBER).getvalue()[0]
            
            conn.commit()
            cursor.close()
            db.pool.release(conn)
            
            return comment_id
            
        except Exception as e:
            logger.error(f"Erro ao salvar comentário: {e}")
            if conn:
                conn.rollback()
                db.pool.release(conn)
            return None
    
    async def get_candidate_comments(self, candidate_id: int) -> List[Dict[str, Any]]:
        """Busca comentários de um candidato"""
        conn = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, comment_text, tags, created_at, created_by
                FROM CANDIDATE_COMMENTS
                WHERE candidate_id = :candidate_id
                ORDER BY created_at DESC
            """, candidate_id=candidate_id)
            
            comments = []
            for row in cursor.fetchall():
                tags = row[2].split(", ") if row[2] else []
                comments.append({
                    "id": row[0],
                    "comment": row[1],
                    "tags": tags,
                    "created_at": row[3],
                    "created_by": row[4]
                })
            
            cursor.close()
            db.pool.release(conn)
            
            return comments
            
        except Exception as e:
            logger.error(f"Erro ao buscar comentários: {e}")
            if conn:
                db.pool.release(conn)
            return []


    async def create_user(
        self,
        nome: str,
        email: str,
        role: str,
        senha_hash: Optional[str] = None,
        cpf: Optional[str] = None,
        telefone: Optional[str] = None,
        data_nascimento: Optional[str] = None,
        linkedin_url: Optional[str] = None
    ) -> Optional[int]:
        """Cria um novo usuário usando PRC_INSERT_USER"""
        conn = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            user_id_var = cursor.var(oracledb.NUMBER)
            
            # Converter data se fornecida
            data_nasc = None
            if data_nascimento:
                try:
                    from datetime import datetime
                    data_nasc = datetime.strptime(data_nascimento, "%Y-%m-%d")
                except:
                    data_nasc = None
            
            cursor.execute("""
                BEGIN
                    PRC_INSERT_USER(
                        p_nome => :nome,
                        p_email => :email,
                        p_role => :role,
                        p_senha_hash => :senha_hash,
                        p_cpf => :cpf,
                        p_telefone => :telefone,
                        p_data_nascimento => :data_nascimento,
                        p_linkedin_url => :linkedin_url,
                        p_user_id => :user_id
                    );
                END;
            """, {
                "nome": nome,
                "email": email,
                "role": role,
                "senha_hash": senha_hash,
                "cpf": cpf,
                "telefone": telefone,
                "data_nascimento": data_nasc,
                "linkedin_url": linkedin_url,
                "user_id": user_id_var
            })
            
            user_id = user_id_var.getvalue()[0] if user_id_var.getvalue() else None
            
            conn.commit()
            cursor.close()
            db.pool.release(conn)
            
            return user_id
            
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {e}")
            if conn:
                conn.rollback()
                db.pool.release(conn)
            return None
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Busca um usuário por ID"""
        conn = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, nome, email, role, telefone, data_nascimento, linkedin_url, created_at
                FROM USERS
                WHERE id = :user_id
            """, user_id=user_id)
            
            row = cursor.fetchone()
            if not row:
                return None
            
            user = {
                "id": row[0],
                "nome": row[1],
                "email": row[2],
                "role": row[3],
                "telefone": row[4],
                "data_nascimento": row[5],
                "linkedin_url": row[6],
                "created_at": row[7]
            }
            
            cursor.close()
            db.pool.release(conn)
            
            return user
            
        except Exception as e:
            logger.error(f"Erro ao buscar usuário: {e}")
            if conn:
                db.pool.release(conn)
            return None
    
    async def list_users(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista todos os usuários, opcionalmente filtrado por role"""
        conn = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if role:
                cursor.execute("""
                    SELECT id, nome, email, role, telefone, data_nascimento, linkedin_url, created_at
                    FROM USERS
                    WHERE role = :role
                    ORDER BY nome
                """, role=role)
            else:
                cursor.execute("""
                    SELECT id, nome, email, role, telefone, data_nascimento, linkedin_url, created_at
                    FROM USERS
                    ORDER BY nome
                """)
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    "id": row[0],
                    "nome": row[1],
                    "email": row[2],
                    "role": row[3],
                    "telefone": row[4],
                    "data_nascimento": row[5],
                    "linkedin_url": row[6],
                    "created_at": row[7]
                })
            
            cursor.close()
            db.pool.release(conn)
            
            return users
            
        except Exception as e:
            logger.error(f"Erro ao listar usuários: {e}")
            if conn:
                db.pool.release(conn)
            return []
    
    async def create_job(
        self,
        titulo: str,
        descricao: Optional[str] = None,
        salario: Optional[float] = None,
        localizacao: Optional[str] = None,
        tipo_contrato: Optional[str] = None,
        nivel: Optional[str] = None,
        modelo_trabalho: Optional[str] = None,
        departamento: Optional[str] = None
    ) -> Optional[int]:
        """Cria uma nova vaga usando PRC_INSERT_JOB"""
        conn = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            job_id_var = cursor.var(oracledb.NUMBER)
            
            cursor.execute("""
                BEGIN
                    PRC_INSERT_JOB(
                        p_titulo => :titulo,
                        p_descricao => :descricao,
                        p_salario => :salario,
                        p_localizacao => :localizacao,
                        p_tipo_contrato => :tipo_contrato,
                        p_nivel => :nivel,
                        p_modelo_trabalho => :modelo_trabalho,
                        p_departamento => :departamento,
                        p_job_id => :job_id
                    );
                END;
            """, {
                "titulo": titulo,
                "descricao": descricao,
                "salario": salario,
                "localizacao": localizacao,
                "tipo_contrato": tipo_contrato,
                "nivel": nivel,
                "modelo_trabalho": modelo_trabalho,
                "departamento": departamento,
                "job_id": job_id_var
            })
            
            job_id = job_id_var.getvalue()[0] if job_id_var.getvalue() else None
            
            conn.commit()
            cursor.close()
            db.pool.release(conn)
            
            return job_id
            
        except Exception as e:
            logger.error(f"Erro ao criar vaga: {e}")
            if conn:
                conn.rollback()
                db.pool.release(conn)
            return None
    
    async def list_jobs(self) -> List[Dict[str, Any]]:
        """Lista todas as vagas"""
        conn = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, titulo, descricao, salario, localizacao, tipo_contrato, 
                       nivel, modelo_trabalho, departamento, created_at
                FROM JOBS
                ORDER BY created_at DESC
            """)
            
            jobs = []
            for row in cursor.fetchall():
                # Converter LOB para string se necessário
                descricao = row[2]
                if descricao is not None:
                    if isinstance(descricao, oracledb.LOB):
                        descricao = descricao.read()
                    elif hasattr(descricao, 'read'):
                        descricao = descricao.read()
                    descricao = str(descricao) if descricao else ""
                else:
                    descricao = ""
                
                job = {
                    "id": row[0],
                    "titulo": row[1],
                    "descricao": descricao,
                    "salario": row[3],
                    "localizacao": row[4],
                    "tipo_contrato": row[5],
                    "nivel": row[6],
                    "modelo_trabalho": row[7],
                    "departamento": row[8],
                    "created_at": row[9],
                    "required_skills": []
                }
                
                # Buscar skills da vaga
                cursor2 = conn.cursor()
                cursor2.execute("""
                    SELECT s.nome
                    FROM JOB_SKILLS js
                    INNER JOIN SKILLS s ON js.skill_id = s.id
                    WHERE js.job_id = :job_id
                """, job_id=row[0])
                
                job["required_skills"] = [r[0] for r in cursor2.fetchall()]
                cursor2.close()
                
                jobs.append(job)
            
            cursor.close()
            db.pool.release(conn)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Erro ao listar vagas: {e}")
            if conn:
                db.pool.release(conn)
            return []
    
    async def add_skill_to_candidate(
        self,
        user_id: int,
        skill_id: int,
        nivel_proficiencia: Optional[float] = None
    ) -> Optional[int]:
        """Adiciona skill a candidato usando PRC_INSERT_CANDIDATE_SKILL"""
        conn = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            candidate_skill_id_var = cursor.var(oracledb.NUMBER)
            
            cursor.execute("""
                BEGIN
                    PRC_INSERT_CANDIDATE_SKILL(
                        p_user_id => :user_id,
                        p_skill_id => :skill_id,
                        p_nivel_proficiencia => :nivel_proficiencia,
                        p_candidate_skill_id => :candidate_skill_id
                    );
                END;
            """, {
                "user_id": user_id,
                "skill_id": skill_id,
                "nivel_proficiencia": nivel_proficiencia,
                "candidate_skill_id": candidate_skill_id_var
            })
            
            candidate_skill_id = candidate_skill_id_var.getvalue()[0] if candidate_skill_id_var.getvalue() else None
            
            conn.commit()
            cursor.close()
            db.pool.release(conn)
            
            return candidate_skill_id
            
        except Exception as e:
            logger.error(f"Erro ao adicionar skill ao candidato: {e}")
            if conn:
                conn.rollback()
                db.pool.release(conn)
            return None
    
    async def add_skill_to_job(
        self,
        job_id: int,
        skill_id: int,
        obrigatoria: bool = True
    ) -> Optional[int]:
        """Adiciona skill a uma vaga"""
        conn = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Verificar se já existe
            cursor.execute("""
                SELECT COUNT(*) FROM JOB_SKILLS
                WHERE job_id = :job_id AND skill_id = :skill_id
            """, job_id=job_id, skill_id=skill_id)
            
            if cursor.fetchone()[0] > 0:
                cursor.close()
                db.pool.release(conn)
                return None  # Já existe
            
            # Inserir
            job_skill_id_var = cursor.var(oracledb.NUMBER)
            cursor.execute("""
                INSERT INTO JOB_SKILLS (job_id, skill_id, obrigatoria)
                VALUES (:job_id, :skill_id, :obrigatoria)
                RETURNING id INTO :job_skill_id
            """, {
                "job_id": job_id,
                "skill_id": skill_id,
                "obrigatoria": 'S' if obrigatoria else 'N',
                "job_skill_id": job_skill_id_var
            })
            
            job_skill_id = job_skill_id_var.getvalue()[0] if job_skill_id_var.getvalue() else None
            
            conn.commit()
            cursor.close()
            db.pool.release(conn)
            
            return job_skill_id
            
        except Exception as e:
            logger.error(f"Erro ao adicionar skill à vaga: {e}")
            if conn:
                conn.rollback()
                db.pool.release(conn)
            return None
    
    async def list_skills(self) -> List[Dict[str, Any]]:
        """Lista todas as skills"""
        conn = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, codigo, nome, categoria, descricao
                FROM SKILLS
                ORDER BY categoria, nome
            """)
            
            skills = []
            for row in cursor.fetchall():
                skills.append({
                    "id": row[0],
                    "codigo": row[1],
                    "nome": row[2],
                    "categoria": row[3],
                    "descricao": row[4]
                })
            
            cursor.close()
            db.pool.release(conn)
            
            return skills
            
        except Exception as e:
            logger.error(f"Erro ao listar skills: {e}")
            if conn:
                db.pool.release(conn)
            return []
    
    async def get_candidate_profile_json(self, candidate_id: int) -> Optional[str]:
        """Obtém perfil do candidato em JSON usando FN_CANDIDATE_PROFILE_AS_JSON"""
        conn = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT FN_CANDIDATE_PROFILE_AS_JSON(:candidate_id) FROM DUAL
            """, candidate_id=candidate_id)
            
            row = cursor.fetchone()
            if not row or not row[0]:
                return None
            
            profile_json = row[0].read() if hasattr(row[0], 'read') else str(row[0])
            
            cursor.close()
            db.pool.release(conn)
            
            return profile_json
            
        except Exception as e:
            logger.error(f"Erro ao buscar perfil JSON: {e}")
            if conn:
                db.pool.release(conn)
            return None
    
    async def calculate_compatibility(self, candidate_id: int, job_id: int) -> Optional[str]:
        """Calcula compatibilidade usando FN_CALC_COMPATIBILITY"""
        conn = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT FN_CALC_COMPATIBILITY(:candidate_id, :job_id) FROM DUAL
            """, candidate_id=candidate_id, job_id=job_id)
            
            row = cursor.fetchone()
            if not row or not row[0]:
                return None
            
            compatibility_json = row[0].read() if hasattr(row[0], 'read') else str(row[0])
            
            cursor.close()
            db.pool.release(conn)
            
            return compatibility_json
            
        except Exception as e:
            logger.error(f"Erro ao calcular compatibilidade: {e}")
            if conn:
                db.pool.release(conn)
            return None


# Instância global do serviço de banco
db_service = DatabaseService()

