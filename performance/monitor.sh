#!/bin/bash
# monitor.sh - GesCol SRE Toolkit
# Monitora uso de recursos do Gunicorn, Uvicorn e conexões do PostgreSQL

METRICS_FILE="metrics.csv"
PID_FILE=".monitor.pid"

start_monitor() {
    echo "Timestamp,CPU_Percent,Memory_MB,Disk_IO_KB_s,DB_Connections" > "$METRICS_FILE"
    
    # Armazena estado inicial dos discos para calcular I/O (deltas)
    prev_disk=$(awk '/[0-9] sd[a-z] / {sum += $6 + $10} END {print sum}' /proc/diskstats)
    if [ -z "$prev_disk" ]; then prev_disk=0; fi

    while true; do
        timestamp=$(date "+%Y-%m-%d %H:%M:%S")
        
        # CPU e Memória (MB) agregada para os workers e o banco
        read cpu_sum mem_sum <<< $(ps -e -o comm,%cpu,rss | awk '
            /gunicorn|uvicorn|postgres|python/ {
                cpu += $2
                mem += $3
            } END {
                print (cpu == "") ? 0 : cpu, (mem == "") ? 0 : mem / 1024
            }')
        
        # Disk IO em KB/s
        curr_disk=$(awk '/[0-9] sd[a-z] / {sum += $6 + $10} END {print sum}' /proc/diskstats)
        if [ -z "$curr_disk" ]; then curr_disk=0; fi
        disk_io=$(( (curr_disk - prev_disk) / 2 )) 
        prev_disk=$curr_disk
        if [ $disk_io -lt 0 ]; then disk_io=0; fi
        
        # Contagem de conexões TCP estabelecidas no Postgres (porta 5432)
        db_conns=$(ss -tn state established | grep -c ":5432")
        
        echo "$timestamp,$cpu_sum,$mem_sum,$disk_io,$db_conns" >> "$METRICS_FILE"
        
        # Fator de coleta: 1 segundo, como requisitado 
        sleep 1
    done
}

if [ "$1" == "start" ]; then
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Monitoramento já está rodando (PID $(cat $PID_FILE))."
        exit 1
    fi
    echo "🚀 Iniciando monitoramento de hardware SRE..."
    echo "📁 Coletando métricas para $METRICS_FILE."
    start_monitor &
    echo $! > "$PID_FILE"
    echo "✅ Monitor executando em background (PID $(cat $PID_FILE))."
    echo "Para parar: ./monitor.sh stop"
elif [ "$1" == "stop" ]; then
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        kill "$pid" 2>/dev/null
        rm "$PID_FILE"
        echo "🛑 Monitoramento interrompido (PID $pid)."
        echo "💡 Dica: Use 'python3 analyze_metrics.py' para gerar o Dashboard."
    else
        echo "Nenhum monitor rodando no momento."
    fi
else
    echo "Uso: $0 {start|stop}"
fi
