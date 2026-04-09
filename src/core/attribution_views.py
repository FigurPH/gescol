"""Fragmentos HTML da tela de Atribuições de Equipamentos.

Toda string HTML gerada dinamicamente para as rotas de atribuição
vive aqui, mantendo o ``atribuicoes_route.py`` focado apenas na lógica
de negócio e no flow de dados.

Nomenclatura:
  - ``error_*``   → erros de validação (badge vermelho/badge-inactive).
  - ``info_*``    → informações neutras / estados do colaborador.
  - ``success_*`` → confirmações de operação bem-sucedida.
  - ``Scripts``   → classe interna com os blocos <script> reutilizáveis.
"""
from __future__ import annotations

from fastapi.responses import HTMLResponse


# ---------------------------------------------------------------------------
# Scripts JS reutilizáveis (sem HTML ao redor)
# ---------------------------------------------------------------------------

class _Scripts:
    """Blocos <script> injetados junto com as respostas HTML."""

    # Foca o campo de matrícula para nova leitura
    RESET_FORM = """
        <script>
            document.getElementById('registration').value = '';
            document.getElementById('serialnumber').value = '';
            document.getElementById('employee-result').innerHTML = `
                <div style="text-align: center; color: #999; padding: 20px;">
                    <p style="font-size: 3rem; margin-bottom: 10px;">👤</p>
                    <p>Aguardando leitura da matrícula...</p>
                </div>
            `;
            document.getElementById('registration').focus();
        </script>
    """

    # Versão do reset que também restaura o botão para o fluxo de entrega
    RESET_FORM_FULL = """
        <script>
            document.getElementById('registration').value = '';
            document.getElementById('serialnumber').value = '';
            document.getElementById('employee-result').innerHTML = `
                <div style="text-align: center; color: #999; padding: 20px;">
                    <p style="font-size: 3rem; margin-bottom: 10px;">👤</p>
                    <p>Aguardando leitura da matrícula...</p>
                </div>
            `;
            document.getElementById('registration').focus();
            document.querySelector('button[type="submit"]').textContent = 'Confirmar Entrega';
            document.querySelector('button[type="submit"]').style.background = 'var(--magalu-blue)';
            document.querySelector('form').setAttribute('hx-post', '/atribuicoes/salvar');
            document.getElementById('serialnumber').disabled = false;
        </script>
    """

    # Foca o campo de serialnumber e limpa o valor (re-entrada após erro)
    FOCUS_SERIALNUMBER = (
        "<script>"
        "document.getElementById('serialnumber').value = ''; "
        "document.getElementById('serialnumber').focus();"
        "</script>"
    )

    # Foca o campo de serialnumber sem limpar
    FOCUS_SERIALNUMBER_KEEP = (
        "<script>document.getElementById('serialnumber').focus();</script>"
    )

    # Limpa a mensagem de attribution-message
    CLEAR_ATTRIBUTION_MSG = (
        "<script>document.getElementById('attribution-message').innerHTML = '';</script>"
    )


# ---------------------------------------------------------------------------
# Classe pública de fragmentos
# ---------------------------------------------------------------------------

class AttributionViews:
    """Fábrica de HTMLResponse para todas as telas de atribuição/devolução."""

    # ------------------------------------------------------------------ #
    # Erros gerais (badge-inactive)                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def error_invalid_registration() -> HTMLResponse:
        return HTMLResponse(
            "<div class='badge-inactive' style='width:100%; height:100%; "
            "display:flex; align-items:center, justify-content:center'>"
            "⚠️ Matrícula inválida</div>"
        )

    @staticmethod
    def error_employee_not_found() -> HTMLResponse:
        return HTMLResponse("""
            <div style="text-align: center; color: #d32f2f; padding: 20px;">
                <p style="font-size: 3rem; margin-bottom: 10px;">🚫</p>
                <p><b>Colaborador não encontrado!</b></p>
                <p style="font-size: 0.9rem;">Verifique a matrícula digitada.</p>
            </div>
        """)

    @staticmethod
    def error_cd_mismatch(employee_cd: str) -> HTMLResponse:
        return HTMLResponse(f"""
            <div style="text-align: center; color: #f57c00; padding: 20px;">
                <p style="font-size: 3rem; margin-bottom: 10px;">⚠️</p>
                <p><b>Acesso Negado</b></p>
                <p style="font-size: 0.9rem;">Este colaborador pertence ao CD {employee_cd}.</p>
            </div>
        """)

    @staticmethod
    def error_no_employee_selected() -> HTMLResponse:
        return HTMLResponse("<div class='badge-inactive'>⚠️ Por favor, identifique o colaborador primeiro!</div>")

    @staticmethod
    def error_no_serialnumber() -> HTMLResponse:
        return HTMLResponse(
            f"<div class='badge-inactive'>⚠️ Informe o número de série do equipamento!</div>"
            f"{_Scripts.FOCUS_SERIALNUMBER_KEEP}"
        )

    @staticmethod
    def error_equipment_not_found(serialnumber: str) -> HTMLResponse:
        return HTMLResponse(
            f"<div class='badge-inactive'>❌ Equipamento com S/N <b>{serialnumber}</b> não encontrado!</div>"
            f"{_Scripts.FOCUS_SERIALNUMBER}"
        )

    @staticmethod
    def error_equipment_inactive(name: str) -> HTMLResponse:
        return HTMLResponse(
            f"<div class='badge-inactive'>⚠️ Equipamento <b>{name}</b> em manutenção!</div>"
            f"{_Scripts.FOCUS_SERIALNUMBER}"
        )

    @staticmethod
    def error_equipment_in_use() -> HTMLResponse:
        return HTMLResponse(
            f"<div class='badge-inactive'>🚫 Este equipamento já está em uso!</div>"
            f"{_Scripts.FOCUS_SERIALNUMBER}"
        )

    @staticmethod
    def error_employee_already_has_collector() -> HTMLResponse:
        return HTMLResponse(
            f"<div class='badge-inactive'>🚫 Este colaborador já possui um equipamento!</div>"
            f"{_Scripts.FOCUS_SERIALNUMBER}"
        )

    @staticmethod
    def error_employee_lookup_failed() -> HTMLResponse:
        return HTMLResponse(
            f"<div class='badge-inactive'>❌ Colaborador não identificado!</div>"
            f"{_Scripts.FOCUS_SERIALNUMBER}"
        )

    @staticmethod
    def error_attribution_not_identified() -> HTMLResponse:
        return HTMLResponse("<div class='badge-inactive'>❌ Erro ao identificar a atribuição!</div>")

    @staticmethod
    def error_attribution_not_found() -> HTMLResponse:
        return HTMLResponse("<div class='badge-inactive'>❌ Atribuição não encontrada!</div>")

    @staticmethod
    def error_no_return_serialnumber() -> HTMLResponse:
        return HTMLResponse(
            f"<div class='badge-inactive'>⚠️ Informe o número de série para devolver!</div>"
            f"{_Scripts.FOCUS_SERIALNUMBER}"
        )

    @staticmethod
    def error_wrong_equipment(*, informed_sn: str) -> HTMLResponse:
        """Número de série informado não bate com o do equipamento atribuído."""
        msg_employee_result = f"""
            <div style="text-align: center; color: #d32f2f; padding: 20px;">
                <p style="font-size: 3rem; margin-bottom: 10px;">🚫</p>
                <p><b>Número de série não confere!</b></p>
                <p style="font-size: 0.9rem;">
                    O S/N <b>{informed_sn}</b> não corresponde ao equipamento atribuído a este colaborador.
                </p>
            </div>
        """

        return HTMLResponse(f"""
            <div class='badge-inactive'>❌ O S/N informado não corresponde ao equipamento atribuído!</div>
            <script>
                document.getElementById('employee-result').innerHTML = `{msg_employee_result}`;
                document.getElementById('serialnumber').value = '';
                document.getElementById('serialnumber').focus();
            </script>
        """)


    # ------------------------------------------------------------------ #
    # Estados do colaborador (lookup)                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def info_employee_with_collector(
        *,
        employee_id: int,
        employee_name: str,
        attribution_id: int,
        checkout_time: str,
        collector_name: str | None,
        equipment_type: str | None,
        show_collector_name: bool,
    ) -> HTMLResponse:
        """Colaborador já tem um equipamento ativo → modo devolução."""
        type_label = equipment_type.capitalize() if equipment_type else "Equipamento"
        if show_collector_name and collector_name:
            collector_info = f"<p style='color: #666;'>Possui o {type_label}: <b>{collector_name}</b></p>"
        else:
            collector_info = f"<p style='color: #666;'>Possui um {type_label} pendente de devolução</p>"

        return HTMLResponse(f"""
            {_Scripts.CLEAR_ATTRIBUTION_MSG}
            <div style="text-align: center; padding: 20px; width: 100%;
                        border: 2px solid #ffa000; border-radius: 12px; background: #fffcf5;">
                <p style="font-size: 3rem; margin-bottom: 10px;">📱</p>
                <h3 style="color: #e65100; margin-bottom: 5px;">{employee_name}</h3>
                {collector_info}
                <div style="margin-top: 15px; padding: 10px; background: #fff3e0; border-radius: 8px;">
                    <p style="font-size: 0.9rem; color: #e65100;">
                        <b>Status:</b> Em uso desde {checkout_time}
                    </p>
                </div>
                <input type="hidden" name="attribution_id" value="{attribution_id}">
                <input type="hidden" name="employee_id" value="{employee_id}">
                <script>
                    document.querySelector('button[type="submit"]').textContent = 'Confirmar Devolução';
                    document.querySelector('button[type="submit"]').style.background = '#e65100';
                    document.querySelector('form').setAttribute('hx-post', '/atribuicoes/devolver');
                    document.getElementById('serialnumber').disabled = false;
                    document.getElementById('serialnumber').value = '';
                    document.getElementById('serialnumber').focus();
                </script>
            </div>
        """)

    @staticmethod
    def info_employee_ready(
        *,
        employee_id: int,
        employee_name: str,
        employee_role: str,
        employee_cd: str,
    ) -> HTMLResponse:
        """Colaborador sem equipamento ativo → pronto para receber → modo entrega."""
        return HTMLResponse(f"""
            {_Scripts.CLEAR_ATTRIBUTION_MSG}
            <div style="text-align: center; padding: 20px; width: 100%;">
                <p style="font-size: 3rem; margin-bottom: 10px;">✅</p>
                <h3 style="color: var(--magalu-blue); margin-bottom: 5px;">{employee_name}</h3>
                <p style="color: #666; font-size: 1.1rem; margin-bottom: 5px;">
                    <b>Cargo:</b> {employee_role}
                </p>
                <p style="color: #666;"><b>CD:</b> {employee_cd}</p>
                <input type="hidden" name="employee_id" value="{employee_id}">
                <script>
                    document.querySelector('button[type="submit"]').textContent = 'Confirmar Entrega';
                    document.querySelector('button[type="submit"]').style.background = 'var(--magalu-blue)';
                    document.querySelector('form').setAttribute('hx-post', '/atribuicoes/salvar');
                    document.getElementById('serialnumber').disabled = false;
                    document.getElementById('serialnumber').value = '';
                </script>
            </div>
        """)

    # ------------------------------------------------------------------ #
    # Confirmações de sucesso                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def success_checkout(equipment_name: str, employee_name: str) -> HTMLResponse:
        """Saída / entrega do equipamento confirmada."""
        return HTMLResponse(f"""
            <div style="background: #e8f5e9; padding: 10px; border-radius: 8px;
                        border: 1px solid #2e7d32; text-align: center;
                        color: #2e7d32; font-size: 0.9rem;">
                <b>Saída Confirmada!</b> {equipment_name} → {employee_name}
            </div>
            {_Scripts.RESET_FORM}
        """)

    @staticmethod
    def success_checkin(equipment_name: str, employee_name: str) -> HTMLResponse:
        """Devolução confirmada — fluxo padrão da tela de atribuições."""
        return HTMLResponse(f"""
            <div style="background: #e3f2fd; padding: 10px; border-radius: 8px;
                        border: 1px solid #1976d2; text-align: center;
                        color: #1976d2; font-size: 0.9rem;">
                <b>Devolução Confirmada!</b> {equipment_name} ← {employee_name}
            </div>
            {_Scripts.RESET_FORM_FULL}
        """)

    @staticmethod
    def success_checkin_from_reports(equipment_name: str, employee_name: str) -> HTMLResponse:
        """Devolução confirmada a partir da tela de relatórios (dispara HX-Trigger)."""
        resp = HTMLResponse(f"""
            <div style="background: #e3f2fd; padding: 10px; border-radius: 8px;
                        border: 1px solid #1976d2; text-align: center;
                        color: #1976d2; font-size: 0.9rem; margin-bottom: 10px;">
                <b>Devolução Confirmada!</b> {equipment_name} ← {employee_name}
            </div>
        """)
        resp.headers["HX-Trigger"] = "refreshReports"
        return resp
