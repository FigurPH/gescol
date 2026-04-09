"""Helper genérico de importação CSV.

Responsável por:
  - Decodificar o conteúdo do arquivo (utf-8 com fallback para latin-1).
  - Iterar as linhas via DictReader com colunas normalizadas.
  - Acumular contadores de sucesso/erro e uma lista de mensagens de erro.
  - Gerar o HTML de feedback padronizado ao final.

Uso:
    result = await CsvImporter.read(file)   # retorna CsvResult
    for row in result.rows:
        ...
    return HTMLResponse(CsvImporter.feedback_html(result, "/cadastros/coletores"))
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from typing import Iterator

from fastapi import UploadFile


@dataclass
class CsvResult:
    rows: list[dict]
    success_count: int = 0
    error_count: int = 0
    errors: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.error_count += 1
        self.errors.append(message)

    def add_success(self) -> None:
        self.success_count += 1


class CsvImporter:
    """Utilitário de leitura e feedback de CSV."""

    @staticmethod
    async def read(file: UploadFile) -> CsvResult:
        """Lê e decodifica o arquivo CSV, retornando um CsvResult com as linhas."""
        content = await file.read()
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1")

        stream = io.StringIO(text)
        reader = csv.DictReader(stream, delimiter=",", quotechar='"')

        # Normaliza nomes de colunas para minúsculo sem espaços
        if reader.fieldnames:
            reader.fieldnames = [f.lower().strip() for f in reader.fieldnames]

        rows = list(reader)
        return CsvResult(rows=rows)

    @staticmethod
    def feedback_html(result: CsvResult, list_url: str, entity_label: str = "Importação") -> str:
        """Gera o bloco HTML de feedback padronizado após a importação."""
        feedback = f"""
            <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; border: 1px solid #2e7d32; margin-bottom: 20px; text-align: center;">
                <p style="font-size: 1.2rem; color: #2e7d32; margin-bottom: 10px;">✅ <b>{entity_label} Concluída!</b></p>
                <div style="display: flex; justify-content: center; gap: 20px; margin-bottom: 10px;">
                    <span style="color: #2e7d32;"><b>Sucesso:</b> {result.success_count}</span>
                    <span style="color: #d32f2f;"><b>Erros:</b> {result.error_count}</span>
                </div>
        """

        if result.errors:
            feedback += """
                <details style="margin-top: 10px; font-size: 0.85rem; text-align: left; background: white; padding: 10px; border-radius: 4px; border: 1px solid #ddd;">
                    <summary style="cursor: pointer; color: #666; font-weight: bold;">Log de Erros (Topo 10)</summary>
                    <ul style="margin-top: 5px; color: #d32f2f; padding-left: 20px;">
            """
            for err in result.errors[:10]:
                feedback += f"<li>{err}</li>"
            if len(result.errors) > 10:
                feedback += "<li>... e mais</li>"
            feedback += "</ul></details>"

        feedback += f"""
                <button class="magalu-btn" style="background: #666; margin-top: 15px; width: auto; padding: 8px 30px;"
                        hx-get="{list_url}" hx-target="#content">Atualizar Lista</button>
            </div>
        """
        return feedback
