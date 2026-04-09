import re

from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from src.auth.dependencies import get_current_admin

from src.core.cd_utils import format_cd
from src.core.csv_importer import CsvImporter
from src.core.templates import templates
from src.database.db_session import get_db
from src.database.models.coletor_model import Coletor

router = APIRouter(prefix="/cadastros/coletores")


@router.get("/", response_class=HTMLResponse)
async def list_collectors(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Lista todos os coletores cadastrados.
    Aplica filtro por CD se o administrador for restrito (nível 9).
    """
    query = select(Coletor).order_by(Coletor.name)
    
    if admin.is_cd_restricted:
        query = query.filter(Coletor.cd == admin.cd)

    result = await db.execute(query)
    collectors = result.scalars().all()

    return templates.TemplateResponse(
        "components/cadastros/coletor/collectors_list.html",
        {
            "request": request,
            "collectors": collectors,
            "admin_cd": admin.cd,
            "user_level": admin.user_level,
        },
    )


@router.post("/salvar")
async def save_collector(
    request: Request,
    name: str = Form(...),
    model: str = Form(...),
    serialnumber: str = Form(...),
    cd: str = Form(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Salva um novo coletor no banco de dados.
    Normaliza o número de série (alfanumérico, uppercase).
    """
    clean_serial = re.sub(r"[^a-zA-Z0-9]", "", serialnumber).upper()
    final_name = name.strip()
    if final_name.upper().startswith("COL"):
        final_name = final_name.upper()

    target_cd = admin.cd if admin.is_cd_restricted else cd

    try:
        db.add(
            Coletor(
                name=final_name,
                model=model.strip(),
                serialnumber=clean_serial,
                cd=target_cd,
                is_active=True,
            )
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return HTMLResponse(
            content=f"""
            <div style="background: #ffecb3; color: #856404; padding: 15px; border-radius: 8px; border: 1px solid #ffeeba; margin-bottom: 20px; text-align: center;">
                <strong>⚠️ Erro:</strong> O Número de Série <b>{serialnumber}</b> já está cadastrado no sistema!
                <button type="button" class="magalu-btn" style="background: #666;" hx-get="/cadastros/coletores" hx-target="#content">Cancelar</button>
            </div>
            """,
            status_code=200,
        )

    return await list_collectors(request, db, admin)


@router.get("/novo", response_class=HTMLResponse)
async def new_collector_form(request: Request, admin=Depends(get_current_admin)):
    """Exibe o formulário para cadastro de um novo coletor."""
    return templates.TemplateResponse(
        "components/cadastros/coletor/collector_form.html",
        {"request": request, "admin_cd": admin.cd, "user_level": admin.user_level},
    )


@router.get("/editar/{collector_id}", response_class=HTMLResponse)
async def edit_collector_form(
    request: Request,
    collector_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Exibe o formulário preenchido para edição de um coletor existente."""
    result = await db.execute(select(Coletor).filter_by(id=collector_id))
    collector = result.scalar_one_or_none()

    if not collector:
        return HTMLResponse("Coletor não encontrado", status_code=404)

    return templates.TemplateResponse(
        "components/cadastros/coletor/collector_form.html",
        {
            "request": request,
            "collector": collector,
            "admin_cd": admin.cd,
            "user_level": admin.user_level,
        },
    )


@router.post("/atualizar/{collector_id}")
async def update_collector(
    request: Request,
    collector_id: int,
    name: str = Form(...),
    model: str = Form(...),
    serialnumber: str = Form(...),
    cd: str = Form(...),
    is_active: bool = Form(True),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Atualiza os dados de um coletor existente."""
    clean_model = re.sub(r"[^a-zA-Z0-9 ]", "", model)
    clean_serial = re.sub(r"[^a-zA-Z0-9]", "", serialnumber).upper()

    target_cd = admin.cd if admin.is_cd_restricted else cd

    try:
        await db.execute(
            update(Coletor)
            .where(Coletor.id == collector_id)
            .values(
                name=name,
                model=clean_model,
                serialnumber=clean_serial,
                cd=target_cd,
                is_active=is_active,
            )
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return HTMLResponse(
            f"<script>alert('Erro: Serial {clean_serial} já existe!');</script>"
        )

    return await list_collectors(request, db, admin)


@router.delete("/excluir/{collector_id}")
async def delete_collector(
    collector_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Exclui um coletor do sistema."""
    query = delete(Coletor).where(Coletor.id == collector_id)
    if admin.is_cd_restricted:
        query = query.where(Coletor.cd == admin.cd)

    await db.execute(query)
    await db.commit()
    return HTMLResponse(status_code=200)


@router.post("/upload-csv")
async def upload_collectors_csv(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Processa upload de CSV para importação em massa de coletores.
    Valida CD para administradores restritos.
    """
    if admin.user_level < 9:
        return HTMLResponse("<div class='badge-inactive'>❌ Acesso Negado!</div>")

    if not file.filename.endswith(".csv"):
        return HTMLResponse(
            "<div class='badge-inactive'>❌ O arquivo deve ser um CSV!</div>"
        )

    try:
        csv_result = await CsvImporter.read(file)
        admin_cd_str = format_cd(admin.cd)

        for i, row in enumerate(csv_result.rows, start=1):
            async with db.begin_nested():
                try:
                    name = row.get("nome") or row.get("name")
                    model = row.get("modelo") or row.get("model")
                    serial = (
                        row.get("serie")
                        or row.get("serial")
                        or row.get("serialnumber")
                        or row.get("serial_number")
                    )
                    cd_value = row.get("cd")

                    if not all([name, model, serial, cd_value]):
                        csv_result.add_error(f"Linha {i}: Dados incompletos")
                        continue

                    target_cd = format_cd(str(cd_value))

                    if admin.is_cd_restricted and target_cd != admin_cd_str:
                        csv_result.add_error(
                            f"Linha {i}: CD {target_cd} não autorizado (Seu CD: {admin_cd_str})"
                        )
                        continue

                    db.add(
                        Coletor(
                            name=str(name).strip(),
                            model=str(model).strip(),
                            serialnumber=str(serial).strip().upper(),
                            cd=target_cd,
                            is_active=True,
                        )
                    )
                    await db.flush()
                    csv_result.add_success()
                except IntegrityError:
                    csv_result.add_error(f"Linha {i}: Série duplicada ({serial})")
                except Exception as e:
                    csv_result.add_error(f"Linha {i}: {str(e)}")

        await db.commit()
        return HTMLResponse(
            CsvImporter.feedback_html(
                csv_result, "/cadastros/coletores", "Importação de Coletores"
            )
        )

    except Exception as e:
        return HTMLResponse(
            f"<div class='badge-inactive'>❌ Erro ao processar arquivo: {str(e)}</div>"
        )

