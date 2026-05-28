from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from datetime import datetime

from modules.dimension_extractor import DimensoesPeca
from modules.excel_reader import ParametrosCusto
from modules.calculator import ResultadoCalculo

COR_PRIMARIA   = colors.HexColor("#1a3a5c")
COR_SECUNDARIA = colors.HexColor("#2e86c1")
COR_DESTAQUE   = colors.HexColor("#e74c3c")
COR_FUNDO      = colors.HexColor("#eaf2fb")
COR_CINZA      = colors.HexColor("#7f8c8d")


def gerar_relatorio(dims: DimensoesPeca,
                    params: ParametrosCusto,
                    res: ResultadoCalculo,
                    caminho_saida: str) -> str:

    doc = SimpleDocTemplate(
        caminho_saida,
        pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm,   bottomMargin=15*mm,
    )

    styles = getSampleStyleSheet()
    elementos = []

    # ── Estilos ──────────────────────────────────
    s_titulo = ParagraphStyle(
        "titulo", parent=styles["Heading1"],
        fontSize=16, textColor=COR_PRIMARIA,
        spaceAfter=2*mm, alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    s_sub = ParagraphStyle(
        "sub", parent=styles["Normal"],
        fontSize=10, textColor=COR_CINZA, alignment=TA_CENTER,
    )
    s_sec = ParagraphStyle(
        "sec", parent=styles["Heading2"],
        fontSize=11, textColor=COR_PRIMARIA,
        fontName="Helvetica-Bold",
        spaceBefore=3*mm, spaceAfter=2*mm,
    )
    s_total = ParagraphStyle(
        "total", parent=styles["Normal"],
        fontSize=14, fontName="Helvetica-Bold",
        textColor=COR_DESTAQUE, alignment=TA_RIGHT,
    )
    s_rodape = ParagraphStyle(
        "rodape", parent=styles["Normal"],
        fontSize=7, textColor=COR_CINZA, alignment=TA_CENTER,
    )

    # ── Cabeçalho ────────────────────────────────
    elementos.append(Paragraph("ORÇAMENTO DE USINAGEM", s_titulo))
    elementos.append(Paragraph(
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", s_sub
    ))
    elementos.append(Spacer(1, 4*mm))
    elementos.append(HRFlowable(width="100%", thickness=2, color=COR_PRIMARIA))
    elementos.append(Spacer(1, 4*mm))

    # ── Seção 1: Identificação ───────────────────
    elementos.append(Paragraph("1. IDENTIFICAÇÃO DA PEÇA", s_sec))
    dados_ident = [
        ["Código da Peça", dims.codigo_peca or "N/D",
         "Cliente",        params.cliente or "N/D"],
        ["Descrição",      dims.descricao or "N/D",
         "Nº Orçamento",   params.numero_orcamento or "N/D"],
        ["Material",       dims.material or "GGG50",
         "Máquina",        params.maquina],
        ["Peso Bruto",     f"{res.peso_bruto_kg:.3f} kg",
         "Peso Final",     f"{res.peso_final_kg:.3f} kg"],
    ]
    elementos.append(_tabela_info(dados_ident))
    elementos.append(Spacer(1, 5*mm))

    # ── Seção 2: Dimensões ───────────────────────
    elementos.append(Paragraph("2. DIMENSÕES DA PEÇA", s_sec))
    dados_dims = [
        ["DIMENSÃO", "VALOR (mm)", "DIMENSÃO", "VALOR (mm)"],
        ["Ø Externo Final",  f"{dims.diametro_externo_mm:.3f}",
         "Ø Bruto (Tarugo)", f"{dims.diametro_externo_mm + 6:.3f}"],
        ["Ø Interno (Furo)", f"{dims.diametro_interno_mm:.3f}" if dims.diametro_interno_mm else "—",
         "Comprimento",      f"{dims.comprimento_mm:.2f}"],
        ["Tolerância Ø",     f"±{dims.tolerancia_diametro:.3f}",
         "Nº de Furos",      str(len(dims.furos_encontrados))],
    ]
    if dims.roscas_encontradas:
        dados_dims.append(["Roscas", ", ".join(dims.roscas_encontradas[:3]), "", ""])
    elementos.append(_tabela_dados(dados_dims))
    elementos.append(Spacer(1, 5*mm))

    # ── Seção 3: Volume ──────────────────────────
    elementos.append(Paragraph("3. VOLUME DE MATERIAL", s_sec))
    aproveit = (
        f"{(res.volume_final_cm3 / res.volume_bruto_cm3 * 100):.1f}%"
        if res.volume_bruto_cm3 > 0 else "N/D"
    )
    dados_vol = [
        ["GRANDEZA", "VALOR"],
        ["Volume do Tarugo Bruto",  f"{res.volume_bruto_cm3:.2f} cm³"],
        ["Volume da Peça Acabada",  f"{res.volume_final_cm3:.2f} cm³"],
        ["Volume Total Removido",   f"{res.volume_removido_cm3:.2f} cm³"],
        ["Aproveitamento do Material", aproveit],
    ]
    elementos.append(_tabela_dados(dados_vol, larguras=[120*mm, 60*mm]))
    elementos.append(Spacer(1, 5*mm))

    # ── Seção 4: Tempo ───────────────────────────
    elementos.append(Paragraph("4. ESTIMATIVA DE TEMPO DE USINAGEM", s_sec))
    dados_tempo = [
        ["OPERAÇÃO", "TEMPO (min)", "OBSERVAÇÃO"],
        ["Torneamento (Desbaste + Acabamento)",
         f"{res.tempo_torneamento_min:.1f}",
         f"Vc={res.velocidade_corte_m_min} m/min | n={res.rotacao_rpm:.0f} RPM"],
        ["Furação / Rosqueamento",
         f"{res.tempo_furos_min:.1f}",
         f"{len(dims.furos_encontrados)} furo(s)"],
        [f"Setup (lote de {params.qtde_lote} pç)",
         f"{res.tempo_setup_rateado_min:.1f}",
         f"Setup total: {params.tempo_setup_min:.0f} min"],
        ["TEMPO TOTAL POR PEÇA",
         f"{res.tempo_total_min:.1f}",
         f"= {res.tempo_total_min/60:.2f} h"],
    ]
    elementos.append(_tabela_dados(
        dados_tempo,
        larguras=[100*mm, 35*mm, 80*mm],
        destaque_ultima=True
    ))
    elementos.append(Spacer(1, 5*mm))

    # ── Seção 5: Custo ───────────────────────────
    elementos.append(Paragraph("5. COMPOSIÇÃO DO CUSTO", s_sec))
    dados_custo = [
        ["COMPONENTE", "BASE DE CÁLCULO", "VALOR (R$)"],
        ["Custo do Material Bruto",
         f"{res.peso_bruto_kg:.3f} kg × R$ {params.custo_material_kg:.2f}/kg",
         f"R$ {res.custo_material:.2f}"],
        ["Custo de Máquina",
         f"{res.tempo_total_min:.1f} min × R$ {params.custo_hora_torno_cnc:.2f}/h",
         f"R$ {res.custo_maquina:.2f}"],
        ["Overhead / Estrutura",
         f"{params.overhead_percentual:.0f}% sobre custo direto",
         f"R$ {res.custo_overhead:.2f}"],
        ["Margem de Lucro",
         f"{params.lucro_percentual:.0f}% sobre custo total",
         f"R$ {res.custo_lucro:.2f}"],
        ["CUSTO TOTAL POR PEÇA", "", f"R$ {res.custo_total:.2f}"],
    ]
    elementos.append(_tabela_dados(
        dados_custo,
        larguras=[80*mm, 95*mm, 40*mm],
        destaque_ultima=True
    ))
    elementos.append(Spacer(1, 8*mm))
    elementos.append(Paragraph(
        f"VALOR TOTAL POR PEÇA: R$ {res.custo_total:.2f}", s_total
    ))

    # ── Seção 6: Notas ───────────────────────────
    if res.notas:
        elementos.append(Spacer(1, 5*mm))
        elementos.append(Paragraph("6. OBSERVAÇÕES", s_sec))
        for nota in res.notas:
            elementos.append(Paragraph(f"• {nota}", styles["Normal"]))

    # ── Rodapé ───────────────────────────────────
    elementos.append(Spacer(1, 10*mm))
    elementos.append(HRFlowable(width="100%", thickness=1, color=COR_CINZA))
    elementos.append(Paragraph(
        f"Sistema de Orçamento de Usinagem | "
        f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
        s_rodape
    ))

    doc.build(elementos)
    return caminho_saida


# ── Helpers ──────────────────────────────────────

def _tabela_info(dados: list) -> Table:
    larguras = [40*mm, 55*mm, 40*mm, 55*mm]
    tab = Table(dados, colWidths=larguras)
    tab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), COR_FUNDO),
        ("BACKGROUND", (2, 0), (2, -1), COR_FUNDO),
        ("TEXTCOLOR",  (0, 0), (0, -1), COR_PRIMARIA),
        ("TEXTCOLOR",  (2, 0), (2, -1), COR_PRIMARIA),
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",   (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("PADDING",    (0, 0), (-1, -1), 4),
    ]))
    return tab


def _tabela_dados(dados: list, larguras=None,
                  destaque_ultima=False) -> Table:
    if larguras is None:
        n_cols = len(dados[0]) if dados else 2
        larguras = [180*mm / n_cols] * n_cols

    tab = Table(dados, colWidths=larguras)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), COR_PRIMARIA),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("PADDING",    (0, 0), (-1, -1), 4),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUND", (0, 1), (-1, -1), [colors.white, COR_FUNDO]),
    ]
    if destaque_ultima:
        estilo += [
            ("BACKGROUND", (0, -1), (-1, -1), COR_PRIMARIA),
            ("TEXTCOLOR",  (0, -1), (-1, -1), colors.white),
            ("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold"),
        ]
    tab.setStyle(TableStyle(estilo))
    return tab