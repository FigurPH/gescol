import random
from locust import HttpUser, task, between, LoadTestShape
from locust.exception import StopUser
from gevent import sleep

class GescolUser(HttpUser):
    # Simula think time de 1 a 5 segundos entre as tarefas
    wait_time = between(1, 5)

    def on_start(self):
        """
        Executado quando o usuário virtual (locust) é iniciado.
        Realiza o fluxo de login inicial.
        Como o servidor possui rate limit de 5 req/min, simulamos 
        com credentials reais ou fazemos um backoff com wait time (sleep).
        """
        self.login()

    def login(self):
        """Realiza o login com tentativas de contornar ou esperar o 429 (Rate Limit)"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            # Sorteamos entre alguns usuários (ex: admin_a, user_b, etc)
            # No nosso db de mock: superadmin, admin_a, user_b
            users_pool = [("superadmin", "pass123"), ("admin_a", "senha1"), ("user_b", "senha2")]
            user_creds = random.choice(users_pool)
            
            response = self.client.post(
                "/auth/login",
                data={"username": user_creds[0], "password": user_creds[1]},
                name="Login",
                allow_redirects=False # HTMX e redirects locais
            )
            
            if response.status_code == 429:
                # Bateu no Rate Limit, dorme e tenta de novo (Backoff)
                sleep_time = 15 * (retry_count + 1)
                print(f"[Locust] Rate Limit 429 - Dormindo {sleep_time}s antes de re-tentar")
                sleep(sleep_time)
                retry_count += 1
            elif response.status_code in [200, 302, 303]:
                # Login efetuado com sucesso (setou cookie)
                return
            else:
                # Outro erro
                print(f"[Locust] Erro no login: {response.status_code} - {response.text}")
                sleep(5)
                retry_count += 1
                
        # Se não logar após os retries, para este usuário para não poluir os logs
        raise StopUser()

    @task(1)
    def view_dashboard(self):
        """Acessa o Dashboard Principal"""
        self.client.get(
            "/dashboard/",
            name="Visualizar Dashboard"
        )

    @task(3)
    def perform_attribution_checkout(self):
        """
        Simula o fluxo de Checkout / Checkin enviando Headres HTMX
        """
        # Simulando randomização de ID de colaborador e Equipamento para bypassar possíveis caches
        employee_id = random.randint(1, 200) # Assumindo 200 colabs na base
        serial_number = f"SN-{random.randint(1000, 9999)}"
        
        headers = {
            "HX-Request": "true"
        }
        
        response = self.client.post(
            "/atribuicoes/salvar",
            data={
                "serialnumber": serial_number,
                "employee_id": employee_id
            },
            headers=headers,
            name="Atribuição (Checkout/CheckinHTMX)"
        )

        # O retorno é um HTML ou badge. 
        if response.status_code != 200:
            print(f"[Locust] Falha em atribuição na rota. Status: {response.status_code}")


class ProgressiveLoadShape(LoadTestShape):
    """
    Modelo de carga progressivo (Step Load).
    O Script escala de 100 usuários para 200.
    """
    
    stages = [
        {"duration": 60, "users": 50, "spawn_rate": 5},   # Warm up
        {"duration": 180, "users": 100, "spawn_rate": 5}, # Primeiro patamar (100)
        {"duration": 300, "users": 150, "spawn_rate": 5}, # Patamar transição (150)
        {"duration": 480, "users": 200, "spawn_rate": 10},# Objetivo máximo (200)
    ]

    def tick(self):
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data
                
        # Se passar do tempo final (480s), termina o teste.
        return None
