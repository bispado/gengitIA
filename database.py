"""
Módulo de conexão com Oracle Database
"""
import oracledb
from typing import Optional
from config import settings
import logging

logger = logging.getLogger(__name__)


class OracleDB:
    """Classe para gerenciar conexões com Oracle Database"""
    
    def __init__(self):
        self.pool: Optional[oracledb.ConnectionPool] = None
    
    def get_connection_string(self) -> str:
        """Retorna a string de conexão formatada"""
        if settings.oracle_connection_string:
            return settings.oracle_connection_string
        return f"{settings.oracle_host}:{settings.oracle_port}/{settings.oracle_sid}"
    
    def create_pool(self):
        """Cria pool de conexões"""
        try:
            self.pool = oracledb.create_pool(
                user=settings.oracle_user,
                password=settings.oracle_password,
                dsn=self.get_connection_string(),
                min=2,
                max=10,
                increment=1
            )
            logger.info("Pool de conexões Oracle criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar pool de conexões: {e}")
            raise
    
    def get_connection(self):
        """Obtém uma conexão do pool"""
        if not self.pool:
            self.create_pool()
        return self.pool.acquire()
    
    def close_pool(self):
        """Fecha o pool de conexões"""
        if self.pool:
            self.pool.close()
            logger.info("Pool de conexões Oracle fechado")


# Instância global do banco de dados
db = OracleDB()

