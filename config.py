import os

# Caminho do Tesseract OCR
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Caminho do Poppler
POPPLER_PATH = r"C:\poppler\poppler-26.02.0\Library\bin"

# Idioma do OCR
OCR_LANG = "por+eng"

# DPI para renderização do PDF
PDF_DPI = 200

# Parâmetros padrão de usinagem
PARAMETROS_DEFAULT = {
    "velocidade_corte_m_min": 80,
    "avanco_mm_rot_desbaste": 0.3,
    "avanco_mm_rot_acabamento": 0.1,
    "prof_corte_desbaste_mm": 2.0,
    "prof_corte_acabamento_mm": 0.3,
    "eficiencia_maquina": 0.75,
    "sobremetal_bruto_mm": 3.0,
    "densidade_kg_cm3": 0.0072,
}