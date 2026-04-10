from fastapi.responses import HTMLResponse

class UIComponents:
    """Componentes UI reutilizáveis para respostas HTMX."""

    @staticmethod
    def error_card(message: str, back_url: str = "/dashboard") -> HTMLResponse:
        """Retorna um card de erro com botão de voltar."""
        return HTMLResponse(f"""
            <div class="welcome-card" style="border-left: 5px solid #d32f2f;">
                <h3 style="color: #d32f2f; margin-bottom: 15px;">❌ Erro</h3>
                <p style="margin-bottom: 20px;">{message}</p>
                <button hx-get="{back_url}" hx-target="#content" class="magalu-btn" 
                        style="background: #666;">
                    Voltar
                </button>
            </div>
        """)

    @staticmethod
    def success_badge(message: str) -> HTMLResponse:
        """Retorna um badge de sucesso verde."""
        return HTMLResponse(f"<div class='badge-active' style='background:#e8f5e9; color:#2e7d32; border:1px solid #2e7d32'>✅ {message}</div>")

    @staticmethod
    def error_badge(message: str) -> HTMLResponse:
        """Retorna um badge de erro vermelho."""
        return HTMLResponse(f"<div class='badge-inactive' style='background:#ffeerr; color:#d32f2f; border:1px solid #d32f2f'>❌ {message}</div>")

    @staticmethod
    def generic_modal_close() -> str:
        """Script para fechar modais (se existirem)."""
        return "<script>document.body.dispatchEvent(new Event('close-modal'));</script>"
