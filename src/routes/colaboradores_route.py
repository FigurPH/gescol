from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.auth.dependencies import get_current_admin
from src.core.cd_utils import format_cd, same_cd
from src.core.csv_importer import CsvImporter
from src.core.templates import templates
from src.database.db_session import get_db
from src.database.models.colaborador_model import Colaborador
from src.core.logger import log
from src.core.ui_components import UIComponents

router = APIRouter(prefix="/colaboradores")


@router.get("/", response_class=HTMLResponse)
async def list_employees(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Lista todos os colaboradores cadastrados.
    Filtra por filial caso o administrador seja restrito (nível 9).
    """
    query = select(Colaborador)
    if admin.is_cd_restricted:
        query = query.filter(Colaborador.filial == format_cd(admin.cd))

    result = await db.execute(query.order_by(Colaborador.name))
    employees = result.scalars().all()

    log.info(
        f"LOG: {admin.username} - Colaboradores listados com sucesso. Total: {len(employees)}"
    )

    return templates.TemplateResponse(
        "components/cadastros/colaborador/employee_list.html",
        {"request": request, "employees": employees, "user_level": admin.user_level},
    )


@router.delete("/excluir/{emp_id}")
async def delete_employee(
    emp_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Remove um colaborador do sistema após validação de permissão por CD."""
    result = await db.execute(select(Colaborador).filter_by(id=emp_id))
    employee = result.scalar_one_or_none()

    if employee:
        if admin.is_cd_restricted and not same_cd(employee.filial, admin.cd):
            log.warning(
                f"LOG: {admin.username} - Tentativa de exclusão negada (CD incompatível): {employee.name}"
            )
            return UIComponents.error_badge("Acesso negado: CD diferente")

        await db.delete(employee)
        await db.commit()

        log.info(f"LOG: {admin.username} - Colaborador {employee.name} excluído")

    return HTMLResponse(status_code=200)


@router.get("/novo", response_class=HTMLResponse)
async def new_employee_form(request: Request, admin=Depends(get_current_admin)):
    """Exibe o formulário de cadastro de novo colaborador."""
    fixed_cd = format_cd(admin.cd) if admin.is_cd_restricted else ""

    return templates.TemplateResponse(
        "components/cadastros/colaborador/employee_form.html",
        {"request": request, "fixed_cd": fixed_cd, "admin_level": admin.user_level},
    )


@router.post("/save")
async def save_employee(
    request: Request,
    id_magalu: int = Form(...),
    name: str = Form(...),
    role: str = Form(...),
    cd: str = Form(...),
    turno: int = Form(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Salva um novo colaborador no banco de dados."""
    target_cd = format_cd(cd)

    if admin.is_cd_restricted and not same_cd(target_cd, admin.cd):
        return UIComponents.error_card("Erro: CD não autorizado.", back_url="/colaboradores")

    try:
        db.add(
            Colaborador(
                matricula=str(id_magalu),
                name=name.strip(),
                cargo=role.strip(),
                filial=target_cd,
                turno=int(turno),
            )
        )
        await db.commit()
        log.info(f"LOG: {admin.username} - Colaborador {name} cadastrado")
    except IntegrityError:
        await db.rollback()
        log.error(f"LOG: {admin.username} - Erro: Matrícula {id_magalu} já existe")
        return UIComponents.error_card("Erro: ID Magalu já cadastrado.", back_url="/colaboradores/novo")

    return await list_employees(request, db, admin)


@router.get("/editar/{emp_id}", response_class=HTMLResponse)
async def edit_employee_form(
    emp_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Exibe o formulário para edição de um colaborador existente."""
    result = await db.execute(select(Colaborador).filter_by(id=emp_id))
    employee = result.scalar_one_or_none()

    if not employee:
        return HTMLResponse("Colaborador não encontrado", status_code=404)

    if admin.is_cd_restricted and not same_cd(employee.filial, admin.cd):
        log.warning(f"LOG: {admin.username} - Acesso negado ao colaborador {employee.name}")
        return UIComponents.error_card("Acesso negado", back_url="/colaboradores")

    return templates.TemplateResponse(
        "components/cadastros/colaborador/employee_edit_form.html",
        {"request": request, "employee": employee, "admin_level": admin.user_level},
    )


@router.post("/update/{emp_id}")
async def update_employee(
    emp_id: int,
    request: Request,
    id_magalu: int = Form(...),
    name: str = Form(...),
    role: str = Form(...),
    cd: str = Form(...),
    turno: int = Form(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Atualiza os dados de um colaborador existente."""
    result = await db.execute(select(Colaborador).filter_by(id=emp_id))
    employee = result.scalar_one_or_none()

    if not employee:
        return UIComponents.error_badge("Erro: Colaborador não encontrado.")

    target_cd = format_cd(cd)

    if admin.is_cd_restricted:
        if not same_cd(employee.filial, admin.cd) or not same_cd(target_cd, admin.cd):
            log.warning(f"LOG: {admin.username} - Tentativa de alteração de CD negada")
            return HTMLResponse(
                "<span style='color:red'>Acesso Negado: Você não pode alterar o CD.</span>"
            )

    employee.matricula = str(id_magalu)
    employee.name = name.strip()
    employee.cargo = role.strip()
    employee.filial = target_cd
    employee.turno = turno

    try:
        await db.commit()
        log.info(f"LOG: {admin.username} - Colaborador {employee.name} atualizado")
    except Exception as e:
        await db.rollback()
        log.error(f"LOG: {admin.username} - Erro ao atualizar: {str(e)}")
        return HTMLResponse(f"<span style='color:red'>Erro ao atualizar: {str(e)}</span>")

    return await list_employees(request, db, admin)


@router.post("/upload-csv")
async def upload_employees_csv(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Processa upload de CSV para importação massiva de colaboradores."""
    if admin.user_level < 9:
        return HTMLResponse("<div class='badge-inactive'>❌ Acesso Negado!</div>")

    if not file.filename.endswith(".csv"):
        return HTMLResponse("<div class='badge-inactive'>❌ O arquivo deve ser um CSV!</div>")

    try:
        csv_result = await CsvImporter.read(file)
        admin_cd_str = format_cd(admin.cd)

        for i, row in enumerate(csv_result.rows, start=1):
            async with db.begin_nested():
                try:
                    matricula = row.get("matricula") or row.get("id_magalu") or row.get("registration")
                    nome = row.get("nome") or row.get("name")
                    cargo = row.get("cargo") or row.get("role")
                    cd_value = row.get("cd")

                    if not all([matricula, nome, cargo, cd_value]):
                        csv_result.add_error(f"Linha {i}: Dados incompletos")
                        continue

                    target_cd = format_cd(str(cd_value))

                    if admin.is_cd_restricted and target_cd != admin_cd_str:
                        csv_result.add_error(
                            f"Linha {i}: CD {target_cd} não autorizado (Seu CD: {admin_cd_str})"
                        )
                        continue

                    db.add(
                        Colaborador(
                            matricula=str(matricula),
                            name=str(nome).strip(),
                            cargo=str(cargo).strip(),
                            filial=target_cd,
                            turno=int(row.get("turno") or 0),
                        )
                    )
                    await db.flush()
                    csv_result.add_success()
                except IntegrityError:
                    csv_result.add_error(f"Linha {i}: Matrícula duplicada ({matricula})")
                except Exception as e:
                    csv_result.add_error(f"Linha {i}: {str(e)}")

        await db.commit()
        log.info(f"LOG: {admin.username} - CSV Importado: {len(csv_result.rows)} linhas processadas")
        
        return HTMLResponse(
            CsvImporter.feedback_html(
                csv_result, "/colaboradores", "Importação de Colaboradores"
            )
        )

    except Exception as e:
        log.error(f"LOG: {admin.username} - Erro no upload CSV: {str(e)}")
        return UIComponents.error_badge(f"Erro: {str(e)}")

