#!/bin/bash

# Script de Orquestração do Stress Test
# Uso: ./run_stress.sh

STRESS_URL="http://localhost:8000"
DURATION="30s"
SPAWN_RATE=1
RESULTS_DIR="performance/results"

mkdir -p $RESULTS_DIR

echo "[STRESS-TEST] Iniciando setup do banco..."
PYTHONPATH=. python3 performance/stress_setup.py

run_wave() {
    USERS=$1
    PREFIX="wave_${USERS}_users"
    echo "----------------------------------------------------"
    echo "[STRESS-TEST] Iniciando Onda: $USERS usuários"
    echo "----------------------------------------------------"
    
    locust -f performance/locustfile.py \
        --headless \
        --users $USERS \
        --spawn-rate $SPAWN_RATE \
        --run-time $DURATION \
        --host $STRESS_URL \
        --csv "$RESULTS_DIR/$PREFIX" \
        --only-summary
    
    echo "[STRESS-TEST] Onda de $USERS concluída. Relatórios em $RESULTS_DIR/"
}

# Ondas de Teste
run_wave 10
run_wave 20
run_wave 50
run_wave 100

echo "[STRESS-TEST] Todos os testes concluídos!"
echo "[STRESS-TEST] Executando teardown..."
PYTHONPATH=. python3 performance/stress_setup.py teardown

echo "[STRESS-TEST] Finalizado."
