import pandas as pd
from dataclasses import dataclass
import os


@dataclass
class ParametrosCusto:
    custo_hora_torno_cnc: float = 85.0
    custo_hora_fresa_cnc: float = 95.0
    custo_hora_retifica: float = 75.0
    custo_hora_setup: float = 50.0
    custo_material_kg: float = 8.50
    overhead_percentual: float = 25.0
    lucro_percentual: float = 15.0
    tempo_setup_min: float = 30.0
    qtde_lote: int = 1
    maquina: str = "CNC TORNO"
    cliente: str = ""
    numero_orcamento: str = ""


def ler_planilha_custos(caminho_xlsx: str,
                        codigo_peca: str = "") -> ParametrosCusto:
    params = ParametrosCusto()

    if not os.path.exists(caminho_xlsx):
        print(f"  ⚠ Planilha não encontrada: {caminho_xlsx}")
        return params

    try:
        df = pd.read_excel(caminho_xlsx, header=None, dtype=str)

        linha_cabecalho = None
        for i, row in df.iterrows():
            row_str = " ".join([str(v) for v in row if str(v) != "nan"])
            if "CLIENTE" in row_str.upper() and "PRODUTO" in row_str.upper():
                linha_cabecalho = i
                break

        if linha_cabecalho is not None:
            df = pd.read_excel(caminho_xlsx,
                               header=linha_cabecalho,
                               dtype=str)
            df.columns = [str(c).strip().upper() for c in df.columns]

            if codigo_peca:
                col_produto = _encontrar_coluna(df, ["PRODUTO", "CÓDIGO", "PEÇA"])
                if col_produto:
                    mascara = df[col_produto].astype(str).str.contains(
                        str(codigo_peca), na=False
                    )
                    linha = df[mascara].head(1)

                    if not linha.empty:
                        col_valor = _encontrar_coluna(
                            df, ["VALOR ORÇADO", "VALOR", "LOTE", "MÊS"]
                        )
                        if col_valor:
                            val_str = str(linha[col_valor].values[0])
                            try:
                                params.custo_material_kg = float(
                                    val_str.replace(",", ".")
                                )
                            except ValueError:
                                pass

                        col_cliente = _encontrar_coluna(df, ["CLIENTE"])
                        if col_cliente:
                            params.cliente = str(
                                linha[col_cliente].values[0]
                            ).strip()

    except Exception as e:
        print(f"  ⚠ Erro ao ler planilha: {e}")
        print("  → Usando parâmetros padrão")

    return params


def _encontrar_coluna(df: pd.DataFrame,
                      candidatos: list) -> str:
    for candidato in candidatos:
        for col in df.columns:
            if candidato in str(col).upper():
                return col
    return None