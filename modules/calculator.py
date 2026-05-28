import math
from dataclasses import dataclass, field


@dataclass
class ResultadoCalculo:
    volume_bruto_cm3: float = 0.0
    volume_final_cm3: float = 0.0
    volume_removido_cm3: float = 0.0
    peso_bruto_kg: float = 0.0
    peso_final_kg: float = 0.0
    tempo_torneamento_min: float = 0.0
    tempo_furos_min: float = 0.0
    tempo_setup_rateado_min: float = 0.0
    tempo_total_min: float = 0.0
    custo_material: float = 0.0
    custo_maquina: float = 0.0
    custo_overhead: float = 0.0
    custo_lucro: float = 0.0
    custo_total: float = 0.0
    rotacao_rpm: float = 0.0
    velocidade_corte_m_min: float = 0.0
    avanco_mm_min: float = 0.0
    notas: list = field(default_factory=list)


def calcular(dims, params):
    from config import PARAMETROS_DEFAULT
    res = ResultadoCalculo()
    p = PARAMETROS_DEFAULT

    De = dims.diametro_externo_mm
    Di = dims.diametro_interno_mm
    L  = dims.comprimento_mm

    if De <= 0:
        res.notas.append("⚠ Diâmetro externo não identificado — usando 100mm")
        De = 100.0
    if L <= 0:
        res.notas.append("⚠ Comprimento não identificado — usando 80mm")
        L = 80.0

    Db  = De + 2 * p["sobremetal_bruto_mm"]
    Lib = L  + p["sobremetal_bruto_mm"]

    # Volumes
    v_bruto_mm3 = math.pi / 4 * (Db ** 2) * Lib
    res.volume_bruto_cm3 = round(v_bruto_mm3 / 1000, 2)

    v_ext_mm3  = math.pi / 4 * (De ** 2) * L
    v_int_mm3  = math.pi / 4 * (Di ** 2) * L if Di > 0 else 0
    v_final_mm3 = v_ext_mm3 - v_int_mm3
    res.volume_final_cm3 = round(v_final_mm3 / 1000, 2)

    res.volume_removido_cm3 = round(
        res.volume_bruto_cm3 - res.volume_final_cm3, 2
    )
    if res.volume_removido_cm3 < 0:
        res.volume_removido_cm3 = 0
        res.notas.append("⚠ Volume removido negativo — verifique dimensões")

    # Pesos
    dens = p["densidade_kg_cm3"]
    res.peso_bruto_kg  = round(res.volume_bruto_cm3 * dens, 3)
    res.peso_final_kg  = round(res.volume_final_cm3 * dens, 3)

    if dims.peso_kg > 0:
        res.peso_final_kg = dims.peso_kg
        res.notas.append(f"ℹ Peso do desenho usado: {dims.peso_kg} kg")

    # Parâmetros de corte
    Vc = p["velocidade_corte_m_min"]
    res.velocidade_corte_m_min = Vc
    n_rpm = (Vc * 1000) / (math.pi * De) if De > 0 else 0
    res.rotacao_rpm = round(n_rpm, 0)

    f_desbaste = n_rpm * p["avanco_mm_rot_desbaste"]
    f_acab     = n_rpm * p["avanco_mm_rot_acabamento"]

    # Tempo torneamento externo
    n_passes_deb = math.ceil(p["sobremetal_bruto_mm"] / p["prof_corte_desbaste_mm"])
    t_deb_ext  = (L / f_desbaste) * n_passes_deb if f_desbaste > 0 else 0
    t_acab_ext = (L / f_acab) if f_acab > 0 else 0

    # Tempo torneamento interno
    t_int = 0
    if Di > 0:
        n_passes_int = math.ceil((De - Di) / 2 / p["prof_corte_desbaste_mm"])
        t_int = (L / f_desbaste) * n_passes_int if f_desbaste > 0 else 0

    t_torn_bruto = t_deb_ext + t_acab_ext + t_int
    res.tempo_torneamento_min = round(
        t_torn_bruto / p["eficiencia_maquina"], 1
    )

    # Tempo furação
    avanco_furo = 0.05
    t_furos = 0
    for furo in dims.furos_encontrados:
        d_furo = furo["diametro"]
        prof   = furo["profundidade"]
        if d_furo > 0 and prof > 0:
            n_furo = (Vc * 1000) / (math.pi * d_furo)
            t_furos += prof / (n_furo * avanco_furo)
    res.tempo_furos_min = round(t_furos / p["eficiencia_maquina"], 1)

    # Setup rateado
    qtde = max(params.qtde_lote, 1)
    res.tempo_setup_rateado_min = round(params.tempo_setup_min / qtde, 1)

    res.tempo_total_min = round(
        res.tempo_torneamento_min
        + res.tempo_furos_min
        + res.tempo_setup_rateado_min, 1
    )

    # Custos
    res.custo_material = round(res.peso_bruto_kg * params.custo_material_kg, 2)

    tempo_h = res.tempo_total_min / 60
    res.custo_maquina = round(tempo_h * params.custo_hora_torno_cnc, 2)

    custo_direto = res.custo_material + res.custo_maquina
    res.custo_overhead = round(custo_direto * params.overhead_percentual / 100, 2)

    custo_sem_lucro = custo_direto + res.custo_overhead
    res.custo_lucro = round(custo_sem_lucro * params.lucro_percentual / 100, 2)

    res.custo_total = round(custo_sem_lucro + res.custo_lucro, 2)

    return res


def resumo_calculo(res):
    linhas = [
        "═══ RESULTADO DO CÁLCULO ═══",
        f"Volume removido  : {res.volume_removido_cm3:.1f} cm³",
        f"Peso bruto       : {res.peso_bruto_kg:.3f} kg",
        f"Rotação          : {res.rotacao_rpm:.0f} RPM",
        f"Tempo torneamento: {res.tempo_torneamento_min:.1f} min",
        f"Tempo furação    : {res.tempo_furos_min:.1f} min",
        f"Tempo setup/peça : {res.tempo_setup_rateado_min:.1f} min",
        f"TEMPO TOTAL/PEÇA : {res.tempo_total_min:.1f} min",
        "───────────────────────────",
        f"Custo material   : R$ {res.custo_material:.2f}",
        f"Custo máquina    : R$ {res.custo_maquina:.2f}",
        f"Overhead         : R$ {res.custo_overhead:.2f}",
        f"Lucro            : R$ {res.custo_lucro:.2f}",
        f"CUSTO TOTAL      : R$ {res.custo_total:.2f}",
    ]
    if res.notas:
        linhas.append("── Notas ──")
        linhas.extend(res.notas)
    return "\n".join(linhas)