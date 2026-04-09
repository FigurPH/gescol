from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

templates = Jinja2Templates(directory="src/templates")

def zfill_filter(value, width):
    return str(value).zfill(width)

templates.env.filters["zfill"] = zfill_filter


def spa_response(request: Request, component: str, context: dict) -> HTMLResponse:
    """Retorna o componente parcial para requisições HTMX ou o index.html completo
    para acesso direto (F5), injetando ``partial_template`` no contexto.

    Example::

        return spa_response(request, "components/dashboard.html", context)
    """
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(component, context)

    context = {**context, "partial_template": component}
    return templates.TemplateResponse("index.html", context)


def toast_response(message: str, is_error: bool = True, status_code: int = 200) -> HTMLResponse:
    """Gera um Toast via HTMX OOB (Out-Of-Band) de forma limpa, substituindo popup js puro."""
    color = "#f44336" if is_error else "#4caf50"
    html = f"""
    <div id="toast-container" hx-swap-oob="beforeend">
        <div class="toast-message" style="background: {color}; color: white; padding: 15px 20px; border-radius: 4px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; align-items: center; justify-content: space-between; min-width: 250px; animation: slideInX 0.3s ease-out forwards;">
            <span>{message}</span>
            <span onclick="this.parentElement.remove()" style="cursor: pointer; font-weight: bold; margin-left: 15px;">✕</span>
        </div>
        <script>
            setTimeout(() => {{
                const toasts = document.querySelectorAll('.toast-message');
                if (toasts.length > 0) {{
                    const lastToast = toasts[toasts.length - 1];
                    if(lastToast) lastToast.remove();
                }}
            }}, 4000);
        </script>
    </div>
    """
    return HTMLResponse(content=html, status_code=status_code)
