# ⚙️ Sistema de Orçamento de Usinagem

Sistema desktop desenvolvido em Python para automatizar o cálculo de custo de peças de usinagem a partir de desenhos técnicos em PDF.

## 🎯 O que o sistema faz

- Lê desenhos técnicos em **PDF, JPG ou PNG**
- Extrai automaticamente dimensões da peça via **OCR**
- Calcula **volume de material removido**
- Estima o **tempo de usinagem** com base em parâmetros de corte
- Gera um **relatório de orçamento em PDF** profissional

## 🖥️ Interface

Interface gráfica desktop (Tkinter) com 4 abas:
- **Entrada** — upload do desenho e correção de dimensões
- **Parâmetros de Custo** — configuração de valores financeiros
- **Resultados** — resumo do cálculo
- **Log** — histórico detalhado do processamento

## 🛠️ Tecnologias utilizadas

| Biblioteca | Função |
|------------|--------|
| Python 3.11+ | Linguagem principal |
| PyMuPDF (fitz) | Leitura e renderização de PDFs |
| Tesseract OCR | Reconhecimento de texto em imagens |
| OpenCV | Pré-processamento de imagem |
| Tkinter | Interface gráfica desktop |
| ReportLab | Geração do relatório PDF |
| Pandas / OpenPyXL | Leitura de planilhas Excel |

## 📋 Pré-requisitos

- Python 3.11+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) instalado em `C:\Program Files\Tesseract-OCR\`
- [Poppler](https://github.com/oschwartz10612/poppler-windows/releases) instalado em `C:\poppler\`

## 🚀 Como executar

```bash
# Clone o repositório
git clone https://github.com/DanielFatec1911/usinagem-sistema.git
cd usinagem-sistema

# Crie o ambiente virtual
python -m venv venv
venv\Scripts\activate

# Instale as dependências
pip install pymupdf pytesseract pillow opencv-python pandas openpyxl reportlab numpy

# Execute
python main.py
```

## 📊 Exemplo de relatório gerado

O sistema gera um PDF com:
- Identificação da peça (código, cliente, material)
- Tabela de dimensões extraídas
- Volume de material removido
- Estimativa de tempo de usinagem
- Composição detalhada do custo (material + máquina + overhead + lucro)

## 🧮 Fórmulas utilizadas

**Rotação (RPM):**

n = (Vc × 1000) / (π × De)

**Tempo de torneamento:**
T = (Comprimento / Avanço_mm_min) × Número_de_passes

**Custo total:**
Custo = Material + Máquina + Overhead% + Lucro%

## 📁 Estrutura do projeto
usinagem_sistema/
├── main.py                      # Interface gráfica principal
├── config.py                    # Configurações globais
├── modules/
│   ├── pdf_reader.py            # Leitura de PDF e OCR
│   ├── dimension_extractor.py   # Extração de dimensões
│   ├── calculator.py            # Cálculos de volume e custo
│   ├── excel_reader.py          # Leitura de planilha Excel
│   └── report_generator.py      # Geração do relatório PDF
└── data/
└── parametros_corte.json    # Parâmetros de usinagem por material

## 👨‍💻 Autor

**Daniel** — [@DanielFatec1911](https://github.com/DanielFatec1911)

Projeto desenvolvido
