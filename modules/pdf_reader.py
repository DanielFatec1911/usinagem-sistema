import fitz
import pytesseract
from PIL import Image
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import TESSERACT_PATH, PDF_DPI, OCR_LANG

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def pdf_para_imagens(caminho_pdf):
    imagens = []
    doc = fitz.open(caminho_pdf)
    zoom = PDF_DPI / 72
    matriz = fitz.Matrix(zoom, zoom)
    for num_pagina in range(len(doc)):
        pagina = doc[num_pagina]
        pixmap = pagina.get_pixmap(matrix=matriz, colorspace=fitz.csRGB)
        img_bytes = pixmap.tobytes("png")
        imagem = Image.open(io.BytesIO(img_bytes))
        imagens.append(imagem)
    doc.close()
    return imagens


def extrair_texto_ocr(imagem):
    import cv2
    import numpy as np

    img_array = np.array(imagem)
    if len(img_array.shape) == 3:
        cinza = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        cinza = img_array

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cinza = clahe.apply(cinza)

    _, binaria = cv2.threshold(cinza, 0, 255,
                               cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    img_processada = Image.fromarray(binaria)
    config_tesseract = "--psm 6 --oem 3"
    texto = pytesseract.image_to_string(
        img_processada,
        lang=OCR_LANG,
        config=config_tesseract
    )
    return texto


def ler_arquivo(caminho):
    extensao = os.path.splitext(caminho)[1].lower()
    imagens = []

    if extensao == ".pdf":
        imagens = pdf_para_imagens(caminho)
    elif extensao in [".jpg", ".jpeg", ".png"]:
        imagens = [Image.open(caminho)]
    else:
        raise ValueError(f"Formato não suportado: {extensao}")

    texto_completo = ""
    for i, img in enumerate(imagens):
        print(f"  -> OCR pagina {i+1}/{len(imagens)}...")
        texto_completo += f"\n--- PAGINA {i+1} ---\n"
        texto_completo += extrair_texto_ocr(img)

    return imagens, texto_completo