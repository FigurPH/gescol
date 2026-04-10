#!/usr/bin/env python3
"""
GesCol SRE Toolkit - Analyze Metrics
Gera um dashboard HTML interativo usando Plotly a partir dos dados do monitor.sh.
"""
import os
import sys

try:
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    print("❌ Dependências não encontradas.")
    print("Para gerar o dashboard, instale os pacotes necessários executando:")
    print("pip install pandas plotly")
    sys.exit(1)

def generate_dashboard(csv_file="metrics.csv", output_html="dashboard.html"):
    if not os.path.exists(csv_file):
        print(f"❌ Erro: Arquivo '{csv_file}' não encontrado.")
        print("💡 Dica: Execute './monitor.sh start' e deixe o Locust rodar para gerar os logs primeiro.")
        return

    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo CSV: {e}")
        return
        
    if df.empty:
        print("⚠️ Aviso: O arquivo metrics.csv está vazio.")
        return

    # Converte coluna de Timestamp
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    # Criação do dashboard com subplots (3 linhas: CPU/Memória, IO, DB Connections)
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(
            "Uso de CPU e Memória (Gunicorn + Postgres + Uvicorn)", 
            "Disk I/O Aggregated (KB/s)", 
            "Conexões TCP Estabelecidas (DB:5432)"
        )
    )

    # 1A. CPU
    fig.add_trace(go.Scatter(
        x=df['Timestamp'], y=df['CPU_Percent'], 
        name="CPU (%)", line=dict(color="#d32f2f", width=2)
    ), row=1, col=1)

    # 1B. Memória (na mesma linha)
    fig.add_trace(go.Scatter(
        x=df['Timestamp'], y=df['Memory_MB'], 
        name="Memória (MB)", line=dict(color="#1976d2", width=2)
    ), row=1, col=1)

    # 2. Disk I/O
    fig.add_trace(go.Scatter(
        x=df['Timestamp'], y=df['Disk_IO_KB_s'], 
        name="Disk I/O (KB/s)", line=dict(color="#f57c00"), fill='tozeroy'
    ), row=2, col=1)

    # 3. Conexões DB
    fig.add_trace(go.Scatter(
        x=df['Timestamp'], y=df['DB_Connections'], 
        name="Conexões DB", line=dict(color="#388e3c", width=2)
    ), row=3, col=1)

    # Encontrar o pico de conexões DB ou CPU para destacar (Reflete max usuários)
    # Procuramos o momento de maior de conexão com o banco ou de uso do disk
    if df['DB_Connections'].max() > 0:
        peak_idx = df['DB_Connections'].idxmax()
    else:
        peak_idx = df['CPU_Percent'].idxmax()
        
    peak_time = df.loc[peak_idx, 'Timestamp']

    fig.add_vline(x=peak_time, line_width=2, line_dash="dash", line_color="MediumPurple",
                  annotation_text="Pico de Carga", annotation_position="top right")

    # Estilização Global
    fig.update_layout(
        title_text="GesCol - Dashboard SRE de Teste de Carga (Locust)",
        height=900,
        template="plotly_dark", # Tema escuro (SRE friendly)
        hovermode="x unified",
        margin=dict(l=40, r=40, t=80, b=40)
    )

    # Configura eixos unificados (Shared X) e Y starts em 0
    fig.update_yaxes(rangemode="tozero")
    
    # Exporta para um arquivo HTML que embute os scripts plotly (standalone)
    fig.write_html(output_html, include_plotlyjs="cdn")
    
    print(f"✅ Dashboard SRE gerado com sucesso: {output_html}")
    print("➡️  Abra o arquivo no seu navegador para visualizar as métricas.")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "metrics.csv")
    html_path = os.path.join(current_dir, "dashboard.html")
    
    print("⏳ Analisando métricas SRE...")
    generate_dashboard(csv_file=csv_path, output_html=html_path)
