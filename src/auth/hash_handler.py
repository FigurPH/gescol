from passlib.context import CryptContext

from src.core.logger import log

# Configuração do contexto de criptografia
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class HashHandler:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verifica se a senha em texto plano corresponde ao hash.
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except ValueError as e:
            log.error(f"Erro ao verificar senha: {e}")
            # Caso ocorra algum erro de preenchimento ou formato no hash
            return False

    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Gera um hash Bcrypt a partir de uma string.
        O Bcrypt tem um limite de 72 caracteres, o passlib cuida disso,
        mas garantimos que a entrada seja tratada corretamente.
        """
        return pwd_context.hash(password)
