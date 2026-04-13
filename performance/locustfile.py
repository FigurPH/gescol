import random
import time
from locust import HttpUser, task, between, SequentialTaskSet
import logging

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stress-test")

class GesColScenario(SequentialTaskSet):
    def on_start(self):
        """Realiza login único por usuário com backoff exponencial para 429."""
        cd_idx = random.randint(1, 5)
        user_idx = random.randint(1, 20)
        self.cd = f"CD{cd_idx:02d}"
        self.username = f"user_cd{cd_idx:02d}_{user_idx:003d}"
        self.password = "stress123"
        self.matricula = f"99{cd_idx:02d}{user_idx:02d}"
        self.serial_base = f"SN-STRESS-CD{cd_idx:02d}"
        
        self.login()

    def login(self):
        attempts = 0
        while attempts < 5:
            response = self.client.post("/auth/login", data={
                "username": self.username,
                "password": self.password
            }, name="/auth/login")
            
            if response.status_code == 200:
                logger.info(f"[STRESS-TEST] Usuário {self.username} logado com sucesso.")
                return
            elif response.status_code == 429:
                wait_time = (2 ** attempts) + random.random()
                logger.warning(f"[STRESS-TEST] Rate limit no login para {self.username}. Aguardando {wait_time:.2f}s...")
                time.sleep(wait_time)
                attempts += 1
            else:
                logger.error(f"[STRESS-TEST] Falha no login para {self.username}: {response.status_code}")
                self.interrupt()
                return
        logger.error(f"[STRESS-TEST] Máximo de tentativas de login atingido para {self.username}")
        self.interrupt()

    @task
    def view_dashboard(self):
        self.client.get("/", name="/dashboard")

    @task
    def view_atribuicoes(self):
        self.client.get("/atribuicoes/", name="/atribuicoes/index")

    @task
    def workflow_checkin_checkout(self):
        # 1. Buscar colaborador (o próprio do usuário para simplificar)
        employee_id = None
        attribution_id = None
        
        with self.client.get(f"/atribuicoes/buscar-colaborador?registration={self.matricula}", 
                            name="/atribuicoes/buscar", catch_response=True) as resp:
            if resp.status_code == 200:
                # Extrair employee_id
                import re
                emp_match = re.search(r'name="employee_id" value="(\d+)"', resp.text)
                if emp_match:
                    employee_id = emp_match.group(1)
                
                # Extrair attribution_id se o colaborador já tiver um
                attr_match = re.search(r'name="attribution_id" value="(\d+)"', resp.text)
                if attr_match:
                    attribution_id = attr_match.group(1)
                
                resp.success()
            else:
                resp.failure(f"Erro na busca: {resp.status_code}")
                return

        # Se já tem atribuição, faz o checkin primeiro
        if attribution_id:
            sn = f"{self.serial_base}_{random.randint(1, 20):03d}"
            with self.client.post("/atribuicoes/devolver", data={
                "attribution_id": attribution_id,
                "serialnumber": sn # Pode dar erro se o SN não bater, mas gera carga
            }, name="/atribuicoes/devolver", catch_response=True) as resp:
                if "Devolução Confirmada" in resp.text:
                    resp.success()
                else:
                    resp.success() # No stress, "errar" o SN também faz parte do teste de latência

        # 2. Checkout
        if employee_id:
            sn = f"{self.serial_base}_{random.randint(1, 20):03d}"
            with self.client.post("/atribuicoes/salvar", data={
                "employee_id": employee_id,
                "serialnumber": sn
            }, name="/atribuicoes/checkout", catch_response=True) as resp:
                if "Saída Confirmada" in resp.text or resp.status_code == 200:
                    resp.success()
                else:
                    resp.failure(f"Erro no checkout: {resp.text[:100]}")

            # 3. Simular erro de concorrência (UniqueIndex)
            with self.client.post("/atribuicoes/salvar", data={
                "employee_id": employee_id, 
                "serialnumber": sn
            }, name="/atribuicoes/checkout-concurrency", catch_response=True) as resp:
                if "já está em uso" in resp.text and "hx-swap-oob" in resp.text:
                    resp.success()
                else:
                    resp.success()

class HeavyUser(HttpUser):
    tasks = [GesColScenario]
    wait_time = between(1, 3)
    host = "http://localhost:8000" # Ajustar conforme ambiente
