"""
Script para popular o banco de dados com dados de exemplo
Execute: python populate_examples.py
"""
import requests
import json
import time
import sys
import io

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_BASE_URL = "http://localhost:8000"

def print_response(title, response):
    """Imprime resposta formatada"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    if response.status_code in [200, 201]:
        print(f"✅ Sucesso! Status: {response.status_code}")
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    else:
        print(f"❌ Erro! Status: {response.status_code}")
        print(response.text)
        return None

def create_candidate(name, email, cpf, telefone, data_nascimento=None, linkedin_url=None):
    """Cria um candidato"""
    # Verificar se já existe
    check_response = requests.get(f"{API_BASE_URL}/api/users?role=candidate")
    if check_response.status_code == 200:
        existing_users = check_response.json()
        for user in existing_users:
            if user.get("email") == email:
                print(f"  ⚠️ Candidato {name} já existe (email: {email})")
                return user
    
    payload = {
        "nome": name,
        "email": email,
        "role": "candidate",
        "cpf": cpf,
        "telefone": telefone,
        "data_nascimento": data_nascimento,
        "linkedin_url": linkedin_url,
        "senha_hash": "hash_exemplo"
    }
    response = requests.post(f"{API_BASE_URL}/api/users", json=payload)
    return print_response(f"Criando candidato: {name}", response)

def create_job(titulo, descricao, salario, localizacao, tipo_contrato, nivel, modelo_trabalho, departamento):
    """Cria uma vaga"""
    # Verificar se já existe
    check_response = requests.get(f"{API_BASE_URL}/api/jobs")
    if check_response.status_code == 200:
        existing_jobs = check_response.json()
        for job in existing_jobs:
            if job.get("titulo") == titulo:
                print(f"  ⚠️ Vaga '{titulo}' já existe")
                return job
    
    payload = {
        "titulo": titulo,
        "descricao": descricao,
        "salario": salario,
        "localizacao": localizacao,
        "tipo_contrato": tipo_contrato,
        "nivel": nivel,
        "modelo_trabalho": modelo_trabalho,
        "departamento": departamento
    }
    response = requests.post(f"{API_BASE_URL}/api/jobs", json=payload)
    return print_response(f"Criando vaga: {titulo}", response)

def get_skills():
    """Busca skills disponíveis"""
    response = requests.get(f"{API_BASE_URL}/api/skills")
    if response.status_code == 200:
        return response.json()
    return []

def add_skill_to_candidate(candidate_id, skill_id, nivel_proficiencia):
    """Adiciona skill a um candidato"""
    payload = {
        "skill_id": skill_id,
        "nivel_proficiencia": nivel_proficiencia
    }
    response = requests.post(f"{API_BASE_URL}/api/candidates/{candidate_id}/skills", json=payload)
    if response.status_code == 201:
        print(f"  ✅ Skill {skill_id} adicionada ao candidato {candidate_id}")
        return True
    else:
        print(f"  ⚠️ Erro ao adicionar skill: {response.status_code} - {response.text}")
        return False

def add_skill_to_job(job_id, skill_id, obrigatoria=True):
    """Adiciona skill a uma vaga"""
    payload = {
        "skill_id": skill_id,
        "obrigatoria": obrigatoria
    }
    response = requests.post(f"{API_BASE_URL}/api/jobs/{job_id}/skills", json=payload)
    if response.status_code == 201:
        print(f"  ✅ Skill {skill_id} adicionada à vaga {job_id}")
        return True
    else:
        print(f"  ⚠️ Erro ao adicionar skill: {response.status_code} - {response.text}")
        return False

def main():
    print("🚀 Iniciando população do banco de dados com exemplos...")
    print(f"API: {API_BASE_URL}\n")
    
    # Verificar se API está rodando
    try:
        health = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health.status_code != 200:
            print("❌ API não está respondendo. Certifique-se de que está rodando em http://localhost:8000")
            return
    except Exception as e:
        print(f"❌ Erro ao conectar com a API: {e}")
        print("Certifique-se de que a API está rodando em http://localhost:8000")
        return
    
    print("✅ API está respondendo!\n")
    
    # Buscar skills disponíveis
    print("📋 Buscando skills disponíveis...")
    skills = get_skills()
    if not skills:
        print("⚠️ Nenhuma skill encontrada. As skills precisam estar cadastradas no banco.")
        print("Continuando sem adicionar skills...\n")
    else:
        print(f"✅ {len(skills)} skills encontradas\n")
    
    # Criar candidatos
    print("\n" + "="*60)
    print("  CRIANDO CANDIDATOS")
    print("="*60)
    
    candidates = []
    
    # Candidato 1: Desenvolvedor Python Sênior
    candidate1 = create_candidate(
        name="João Silva",
        email="joao.silva@email.com",
        cpf="123.456.789-00",
        telefone="(11) 98765-4321",
        data_nascimento="1990-05-15",
        linkedin_url="https://linkedin.com/in/joaosilva"
    )
    if candidate1:
        candidates.append(candidate1)
    
    time.sleep(0.5)
    
    # Candidato 2: Desenvolvedor Full Stack
    candidate2 = create_candidate(
        name="Maria Santos",
        email="maria.santos@email.com",
        cpf="987.654.321-00",
        telefone="(11) 97654-3210",
        data_nascimento="1992-08-20",
        linkedin_url="https://linkedin.com/in/mariasantos"
    )
    if candidate2:
        candidates.append(candidate2)
    
    time.sleep(0.5)
    
    # Candidato 3: Analista de Dados
    candidate3 = create_candidate(
        name="Pedro Costa",
        email="pedro.costa@email.com",
        cpf="456.789.123-00",
        telefone="(11) 96543-2109",
        data_nascimento="1988-12-10",
        linkedin_url="https://linkedin.com/in/pedrocosta"
    )
    if candidate3:
        candidates.append(candidate3)
    
    time.sleep(0.5)
    
    # Candidato 4: Desenvolvedor Python Pleno
    candidate4 = create_candidate(
        name="Ana Oliveira",
        email="ana.oliveira@email.com",
        cpf="789.123.456-00",
        telefone="(11) 95432-1098",
        data_nascimento="1995-03-25",
        linkedin_url="https://linkedin.com/in/anaoliveira"
    )
    if candidate4:
        candidates.append(candidate4)
    
    time.sleep(0.5)
    
    # Candidato 5: Machine Learning Engineer
    candidate5 = create_candidate(
        name="Carlos Mendes",
        email="carlos.mendes@email.com",
        cpf="321.654.987-00",
        telefone="(11) 94321-0987",
        data_nascimento="1991-07-18",
        linkedin_url="https://linkedin.com/in/carlosmendes"
    )
    if candidate5:
        candidates.append(candidate5)
    
    print(f"\n✅ {len(candidates)} candidatos criados!")
    
    # Adicionar skills aos candidatos (se houver skills disponíveis)
    if skills and candidates:
        print("\n" + "="*60)
        print("  ADICIONANDO SKILLS AOS CANDIDATOS")
        print("="*60)
        
        # Mapear skills por nome (assumindo que existe Python, Machine Learning, SQL, etc.)
        skill_map = {skill["nome"].lower(): skill["id"] for skill in skills}
        
        # Candidato 1: Python Sênior
        if candidates[0] and "python" in skill_map:
            add_skill_to_candidate(candidates[0]["id"], skill_map["python"], 0.95)
        if candidates[0] and "machine learning" in skill_map:
            add_skill_to_candidate(candidates[0]["id"], skill_map["machine learning"], 0.85)
        if candidates[0] and "sql" in skill_map:
            add_skill_to_candidate(candidates[0]["id"], skill_map["sql"], 0.90)
        
        # Candidato 2: Full Stack
        if len(candidates) > 1 and candidates[1]:
            if "python" in skill_map:
                add_skill_to_candidate(candidates[1]["id"], skill_map["python"], 0.80)
            if "javascript" in skill_map:
                add_skill_to_candidate(candidates[1]["id"], skill_map["javascript"], 0.85)
            if "react" in skill_map:
                add_skill_to_candidate(candidates[1]["id"], skill_map["react"], 0.75)
        
        # Candidato 3: Analista de Dados
        if len(candidates) > 2 and candidates[2]:
            if "python" in skill_map:
                add_skill_to_candidate(candidates[2]["id"], skill_map["python"], 0.75)
            if "sql" in skill_map:
                add_skill_to_candidate(candidates[2]["id"], skill_map["sql"], 0.90)
            if "data science" in skill_map:
                add_skill_to_candidate(candidates[2]["id"], skill_map["data science"], 0.85)
        
        # Candidato 4: Python Pleno
        if len(candidates) > 3 and candidates[3]:
            if "python" in skill_map:
                add_skill_to_candidate(candidates[3]["id"], skill_map["python"], 0.85)
            if "django" in skill_map:
                add_skill_to_candidate(candidates[3]["id"], skill_map["django"], 0.80)
        
        # Candidato 5: ML Engineer
        if len(candidates) > 4 and candidates[4]:
            if "python" in skill_map:
                add_skill_to_candidate(candidates[4]["id"], skill_map["python"], 0.90)
            if "machine learning" in skill_map:
                add_skill_to_candidate(candidates[4]["id"], skill_map["machine learning"], 0.95)
            if "deep learning" in skill_map:
                add_skill_to_candidate(candidates[4]["id"], skill_map["deep learning"], 0.85)
    
    # Criar vagas
    print("\n" + "="*60)
    print("  CRIANDO VAGAS")
    print("="*60)
    
    jobs = []
    
    # Vaga 1: Desenvolvedor Python Sênior
    job1 = create_job(
        titulo="Desenvolvedor Python Sênior",
        descricao="Buscamos desenvolvedor Python sênior com experiência em desenvolvimento de APIs, machine learning e arquitetura de sistemas escaláveis. Responsável por liderar projetos técnicos e mentorar desenvolvedores júnior.",
        salario=15000.00,
        localizacao="São Paulo - SP",
        tipo_contrato="CLT",
        nivel="Senior",  # Deve ser: Junior, Pleno ou Senior
        modelo_trabalho="Hibrido",  # Deve ser: Remoto, Hibrido ou Presencial
        departamento="Tecnologia"
    )
    if job1:
        jobs.append(job1)
    
    time.sleep(0.5)
    
    # Vaga 2: Desenvolvedor Full Stack
    job2 = create_job(
        titulo="Desenvolvedor Full Stack",
        descricao="Vaga para desenvolvedor full stack com experiência em Python (backend) e React/JavaScript (frontend). Trabalhará em projetos web modernos e aplicações responsivas.",
        salario=12000.00,
        localizacao="Remoto",
        tipo_contrato="CLT",
        nivel="Pleno",
        modelo_trabalho="Remoto",
        departamento="Tecnologia"
    )
    if job2:
        jobs.append(job2)
    
    time.sleep(0.5)
    
    # Vaga 3: Analista de Dados
    job3 = create_job(
        titulo="Analista de Dados",
        descricao="Analista de dados para trabalhar com grandes volumes de dados, criar dashboards, relatórios e análises estatísticas. Experiência em Python, SQL e ferramentas de BI.",
        salario=10000.00,
        localizacao="São Paulo - SP",
        tipo_contrato="CLT",
        nivel="Pleno",
        modelo_trabalho="Presencial",
        departamento="Analytics"
    )
    if job3:
        jobs.append(job3)
    
    print(f"\n✅ {len(jobs)} vagas criadas!")
    
    # Adicionar skills às vagas
    if skills and jobs:
        print("\n" + "="*60)
        print("  ADICIONANDO SKILLS ÀS VAGAS")
        print("="*60)
        
        skill_map = {skill["nome"].lower(): skill["id"] for skill in skills}
        
        # Vaga 1: Python Sênior
        if jobs[0]:
            if "python" in skill_map:
                add_skill_to_job(jobs[0]["id"], skill_map["python"], obrigatoria=True)
            if "machine learning" in skill_map:
                add_skill_to_job(jobs[0]["id"], skill_map["machine learning"], obrigatoria=True)
            if "sql" in skill_map:
                add_skill_to_job(jobs[0]["id"], skill_map["sql"], obrigatoria=False)
        
        # Vaga 2: Full Stack
        if len(jobs) > 1 and jobs[1]:
            if "python" in skill_map:
                add_skill_to_job(jobs[1]["id"], skill_map["python"], obrigatoria=True)
            if "javascript" in skill_map:
                add_skill_to_job(jobs[1]["id"], skill_map["javascript"], obrigatoria=True)
            if "react" in skill_map:
                add_skill_to_job(jobs[1]["id"], skill_map["react"], obrigatoria=False)
        
        # Vaga 3: Analista de Dados
        if len(jobs) > 2 and jobs[2]:
            if "python" in skill_map:
                add_skill_to_job(jobs[2]["id"], skill_map["python"], obrigatoria=True)
            if "sql" in skill_map:
                add_skill_to_job(jobs[2]["id"], skill_map["sql"], obrigatoria=True)
            if "data science" in skill_map:
                add_skill_to_job(jobs[2]["id"], skill_map["data science"], obrigatoria=False)
    
    # Resumo final
    print("\n" + "="*60)
    print("  ✅ POPULAÇÃO CONCLUÍDA!")
    print("="*60)
    print(f"📊 Resumo:")
    print(f"   • Candidatos criados: {len(candidates)}")
    print(f"   • Vagas criadas: {len(jobs)}")
    print(f"   • Skills disponíveis: {len(skills)}")
    print("\n🎯 Próximos passos:")
    print(f"   • Acesse: http://localhost:8000/docs")
    print(f"   • Teste o ranking: POST /api/candidates/ranking")
    print(f"   • Busque talentos: POST /api/talent-pool/search")
    print("\n💡 Exemplo de ranking:")
    if jobs:
        print(f'   POST /api/candidates/ranking')
        print(f'   {{"job_id": {jobs[0]["id"]}, "limit": 10, "min_compatibility": 50.0}}')
    print("="*60)

if __name__ == "__main__":
    main()

