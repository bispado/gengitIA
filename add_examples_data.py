"""
Script para adicionar dados de exemplo ao banco
Cria apenas o que não existe ainda
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

def get_existing_data():
    """Busca dados existentes"""
    candidates = []
    jobs = []
    skills = []
    
    try:
        r = requests.get(f"{API_BASE_URL}/api/users?role=candidate")
        if r.status_code == 200:
            candidates = r.json()
    except:
        pass
    
    try:
        r = requests.get(f"{API_BASE_URL}/api/jobs")
        if r.status_code == 200:
            jobs = r.json()
    except:
        pass
    
    try:
        r = requests.get(f"{API_BASE_URL}/api/skills")
        if r.status_code == 200:
            skills = r.json()
    except:
        pass
    
    return candidates, jobs, skills

def add_skill_to_candidate(candidate_id, skill_id, nivel):
    """Adiciona skill a candidato"""
    try:
        r = requests.post(
            f"{API_BASE_URL}/api/candidates/{candidate_id}/skills",
            json={"skill_id": skill_id, "nivel_proficiencia": nivel}
        )
        return r.status_code == 201
    except:
        return False

def add_skill_to_job(job_id, skill_id, obrigatoria=True):
    """Adiciona skill a vaga"""
    try:
        r = requests.post(
            f"{API_BASE_URL}/api/jobs/{job_id}/skills",
            json={"skill_id": skill_id, "obrigatoria": obrigatoria}
        )
        return r.status_code == 201
    except:
        return False

def main():
    print("="*60)
    print("  VERIFICANDO DADOS EXISTENTES")
    print("="*60)
    
    candidates, jobs, skills = get_existing_data()
    
    print(f"\n✅ Candidatos encontrados: {len(candidates)}")
    print(f"✅ Vagas encontradas: {len(jobs)}")
    print(f"✅ Skills encontradas: {len(skills)}")
    
    if candidates:
        print("\n📋 Candidatos:")
        for c in candidates[:5]:
            print(f"   • {c.get('nome')} (ID: {c.get('id')}) - {c.get('email')}")
    
    if jobs:
        print("\n📋 Vagas:")
        for j in jobs[:5]:
            print(f"   • {j.get('titulo')} (ID: {j.get('id')}) - {j.get('nivel', 'N/A')}")
    
    if skills:
        print("\n📋 Skills disponíveis:")
        for s in skills[:10]:
            print(f"   • {s.get('nome')} (ID: {s.get('id')})")
        
        # Adicionar skills aos candidatos
        if candidates and skills:
            print("\n" + "="*60)
            print("  ADICIONANDO SKILLS AOS CANDIDATOS")
            print("="*60)
            
            skill_map = {s["nome"].lower(): s["id"] for s in skills}
            
            # Candidato 1 (se existir)
            if len(candidates) > 0:
                c = candidates[0]
                if "python" in skill_map:
                    if add_skill_to_candidate(c["id"], skill_map["python"], 0.9):
                        print(f"  ✅ Python adicionado a {c['nome']}")
            
            # Candidato 2
            if len(candidates) > 1:
                c = candidates[1]
                if "python" in skill_map:
                    if add_skill_to_candidate(c["id"], skill_map["python"], 0.8):
                        print(f"  ✅ Python adicionado a {c['nome']}")
        
        # Adicionar skills às vagas
        if jobs and skills:
            print("\n" + "="*60)
            print("  ADICIONANDO SKILLS ÀS VAGAS")
            print("="*60)
            
            skill_map = {s["nome"].lower(): s["id"] for s in skills}
            
            # Vaga 1 (se existir)
            if len(jobs) > 0:
                j = jobs[0]
                if "python" in skill_map:
                    if add_skill_to_job(j["id"], skill_map["python"], True):
                        print(f"  ✅ Python adicionado à vaga '{j['titulo']}'")
    
    print("\n" + "="*60)
    print("  ✅ RESUMO FINAL")
    print("="*60)
    print(f"📊 Dados no banco:")
    print(f"   • {len(candidates)} candidatos")
    print(f"   • {len(jobs)} vagas")
    print(f"   • {len(skills)} skills")
    print("\n🎯 Próximos passos para apresentação:")
    print(f"   • Acesse: http://localhost:8000/docs")
    if jobs and candidates:
        print(f"   • Teste ranking: POST /api/candidates/ranking")
        print(f'     {{"job_id": {jobs[0]["id"]}, "limit": 5}}')
        print(f"   • Teste busca: POST /api/talent-pool/search")
        print(f'     {{"query": "desenvolvedor Python", "limit": 10}}')
    print("="*60)

if __name__ == "__main__":
    main()

