"""
Configurações da aplicação
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente"""
    
    # Oracle Database
    oracle_user: Optional[str] = None
    oracle_password: Optional[str] = None
    oracle_host: str = "oracle.fiap.com.br"
    oracle_port: int = 1521
    oracle_sid: str = "ORCL"
    oracle_connection_string: Optional[str] = None
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = int(os.getenv("PORT", 8000))  # Azure usa variável PORT
    api_debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Instância global de configurações
settings = Settings()

