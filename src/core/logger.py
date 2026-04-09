import logging, sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


# Caminho para Logs
LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / 'gescol.log'

class CustomLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Evita duplicidade de logs
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        # Formato do Log - Agora incluindo módulo e função
        fmt = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(funcName)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Handler de Arquivo (corrigido maxBytes para 10MB)
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=10*1024*1024, backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(fmt)
        self.logger.addHandler(file_handler)

        # Handler de Console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(fmt)
        self.logger.addHandler(console_handler)

def get_logger(name: str):
    """Fornece um logger configurado para o módulo chamador."""
    return CustomLogger(name).logger

# Instância Global (mantida para compatibilidade, mas agora com melhor formato)
log = get_logger("src.core.logger")
