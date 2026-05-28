import re
from dataclasses import dataclass, field


@dataclass
class DimensoesPeca:
    codigo_peca: str = ""
    descricao: str = ""
    material: str = ""
    peso_kg: float = 0.0
    diametro_externo_mm: float = 0.0
    diametro_interno_mm: float = 0.0
    comprimento_mm: float = 0.0
    diametro_bruto_mm: float = 0.0
    tolerancia_diametro: float = 0.05
    todos_diametros: list = field(default_factory=list)
    todos_raios: list = field(default_factory=list)
    todas_cotas_lineares: list = field(default_factory=list)
    roscas_encontradas: list = field(default_factory=list)
    furos_encontrados: list = field(default_factory=list)
    texto_original: str = ""


def extrair_dimensoes(texto_ocr: str) -> DimensoesPeca:
    dims = DimensoesPeca()
    dims.texto_original = texto_ocr
    texto = texto_ocr.replace(",", ".")

    # Código da peça
    match = re.search(r'(?:CÓDIGO|CODIGO|COD\.?)\s*[:\.]?\s*(\d{4,8})',
                      texto, re.IGNORECASE)
    if match:
        dims.codigo_peca = match.group(1)
    else:
        match = re.search(r'\b(\d{6})\b', texto)
        if match:
            dims.codigo_peca = match.group(1)

    # Descrição
    match = re.search(r'DESCRIÇÃO\s*[:\.]?\s*(.+?)(?:\n|REV\.?)',
                      texto, re.IGNORECASE)
    if match:
        dims.descricao = match.group(1).strip()

    # Material
    match = re.search(r'MATERIAL\s*[:\.]?\s*(.+?)(?:\n|DIMENSÃO)',
                      texto, re.IGNORECASE)
    if match:
        dims.material = match.group(1).strip()

    # Peso
    match = re.search(r'PESO\s*[:\.]?\s*([\d.,]+)\s*kg',
                      texto, re.IGNORECASE)
    if match:
        dims.peso_kg = _to_float(match.group(1))

    # Diâmetros
    padrao_diametro = re.compile(
        r'[ØønQq∅]\s*([\d.]+)',
        re.IGNORECASE
    )
    padrao_diametro_alt = re.compile(
        r'(?:FURAR|FURO|BORE)\s+[ØønQ]?\s*([\d.]+)',
        re.IGNORECASE
    )

    diametros = []
    for match in padrao_diametro.finditer(texto):
        val = _to_float(match.group(1))
        if 1.0 < val < 500.0:
            diametros.append(round(val, 3))

    for match in padrao_diametro_alt.finditer(texto):
        val = _to_float(match.group(1))
        if 1.0 < val < 500.0:
            diametros.append(round(val, 3))

    vistos = set()
    dims.todos_diametros = [
        d for d in diametros
        if not (d in vistos or vistos.add(d))
    ]

    # Diâmetro externo e interno
    if dims.todos_diametros:
        ordenados = sorted(dims.todos_diametros, reverse=True)
        dims.diametro_externo_mm = ordenados[0]
        for d in ordenados[1:]:
            if d < dims.diametro_externo_mm * 0.9:
                dims.diametro_interno_mm = d
                break

    # Raios
    padrao_raio = re.compile(r'[Rr]\s*([\d.]+)', re.IGNORECASE)
    for match in padrao_raio.finditer(texto):
        val = _to_float(match.group(1))
        if 0.1 < val < 100:
            dims.todos_raios.append(round(val, 3))

    # Cotas lineares
    padrao_linear = re.compile(
        r'(?<![ØønQRr\d.])([\d]{2,4}\.[\d]{1,3}|[\d]{2,4})'
        r'(?!\s*[ØønQ%°])',
        re.IGNORECASE
    )
    cotas = []
    for match in padrao_linear.finditer(texto):
        val = _to_float(match.group(1))
        if 3.0 < val < 1000.0 and val not in dims.todos_diametros:
            cotas.append(round(val, 2))
    dims.todas_cotas_lineares = list(dict.fromkeys(cotas))

    if dims.todas_cotas_lineares:
        candidatos = [c for c in dims.todas_cotas_lineares
                      if c < dims.diametro_externo_mm * 2]
        if candidatos:
            dims.comprimento_mm = max(candidatos)
        else:
            dims.comprimento_mm = max(dims.todas_cotas_lineares)

    # Roscas
    padrao_rosca = re.compile(
        r'(\d+/\d+-\d+\s*(?:UNC|UNF|UNEF)|M\d+(?:x[\d.]+)?)',
        re.IGNORECASE
    )
    dims.roscas_encontradas = padrao_rosca.findall(texto)

    # Furos
    padrao_furo = re.compile(
        r'FURAR\s+[ØønQ]?([\d.]+)\s*[xX]\s*([\d.]+)',
        re.IGNORECASE
    )
    for match in padrao_furo.finditer(texto):
        dims.furos_encontrados.append({
            "diametro": _to_float(match.group(1)),
            "profundidade": _to_float(match.group(2))
        })

    # Tolerâncias
    padrao_tol = re.compile(r'[`±]\s*([\d.]+)')
    tolerancias = []
    for match in padrao_tol.finditer(texto):
        val = _to_float(match.group(1))
        if 0.001 < val < 2.0:
            tolerancias.append(val)
    if tolerancias:
        dims.tolerancia_diametro = max(tolerancias)

    return dims


def _to_float(s: str) -> float:
    try:
        return float(str(s).replace(",", ".").strip())
    except (ValueError, AttributeError):
        return 0.0


def resumo_dimensoes(dims: DimensoesPeca) -> str:
    linhas = [
        f"Código da peça : {dims.codigo_peca or 'Não encontrado'}",
        f"Descrição      : {dims.descricao or 'Não encontrada'}",
        f"Material       : {dims.material or 'Não identificado'}",
        f"Peso bruto     : {dims.peso_kg:.2f} kg",
        f"Ø Externo      : {dims.diametro_externo_mm:.2f} mm",
        f"Ø Interno      : {dims.diametro_interno_mm:.2f} mm",
        f"Comprimento    : {dims.comprimento_mm:.2f} mm",
        f"Tolerância Ø   : ±{dims.tolerancia_diametro:.3f} mm",
        f"Roscas         : {', '.join(dims.roscas_encontradas) or 'Nenhuma'}",
        f"Furos          : {len(dims.furos_encontrados)} encontrados",
        f"Todos Ø        : {dims.todos_diametros}",
    ]
    return "\n".join(linhas)