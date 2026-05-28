import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from datetime import datetime

from modules.pdf_reader import ler_arquivo
from modules.dimension_extractor import extrair_dimensoes, resumo_dimensoes
from modules.excel_reader import ler_planilha_custos, ParametrosCusto
from modules.calculator import calcular, resumo_calculo
from modules.report_generator import gerar_relatorio


class AppOrcamento:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sistema de Orçamento de Usinagem v1.0")
        self.root.geometry("900x750")
        self.root.configure(bg="#f0f4f8")

        self.caminho_desenho = tk.StringVar()
        self.caminho_planilha = tk.StringVar()
        self.dims_resultado = None
        self.params_custo = ParametrosCusto()
        self.resultado_calculo = None
        self.vars_edit = {}

        self._construir_interface()

    def _construir_interface(self):
        frame_titulo = tk.Frame(self.root, bg="#1a3a5c", pady=10)
        frame_titulo.pack(fill="x")
        tk.Label(
            frame_titulo,
            text="⚙  SISTEMA DE ORÇAMENTO DE USINAGEM",
            font=("Helvetica", 16, "bold"),
            bg="#1a3a5c", fg="white"
        ).pack()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.aba_entrada = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_entrada, text="📁  Entrada")
        self._aba_entrada()

        self.aba_params = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_params, text="💰  Parâmetros de Custo")
        self._aba_parametros()

        self.aba_result = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_result, text="📊  Resultados")
        self._aba_resultados()

        self.aba_log = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_log, text="📋  Log")
        self._aba_log()

        self.status_var = tk.StringVar(value="Pronto. Selecione um desenho para começar.")
        tk.Label(
            self.root, textvariable=self.status_var,
            relief="sunken", anchor="w",
            bg="#dce9f5", fg="#1a3a5c",
            font=("Helvetica", 9)
        ).pack(fill="x", side="bottom")

    def _aba_entrada(self):
        frame = self.aba_entrada

        grp = ttk.LabelFrame(frame, text="Desenho Técnico (PDF ou Imagem)")
        grp.pack(fill="x", padx=10, pady=8)
        tk.Entry(grp, textvariable=self.caminho_desenho,
                 width=60, state="readonly").pack(side="left", padx=5, pady=8)
        tk.Button(grp, text="Selecionar...",
                  command=self._selecionar_desenho,
                  bg="#2e86c1", fg="white",
                  font=("Helvetica", 9, "bold"),
                  relief="flat", padx=10).pack(side="left", padx=5)

        grp2 = ttk.LabelFrame(frame, text="Planilha de Custos (Excel .xlsx) — opcional")
        grp2.pack(fill="x", padx=10, pady=8)
        tk.Entry(grp2, textvariable=self.caminho_planilha,
                 width=60, state="readonly").pack(side="left", padx=5, pady=8)
        tk.Button(grp2, text="Selecionar...",
                  command=self._selecionar_planilha,
                  bg="#2e86c1", fg="white",
                  font=("Helvetica", 9, "bold"),
                  relief="flat", padx=10).pack(side="left", padx=5)

        tk.Button(
            frame,
            text="🔍   ANALISAR DESENHO E CALCULAR",
            command=self._processar,
            bg="#1a3a5c", fg="white",
            font=("Helvetica", 12, "bold"),
            relief="flat", pady=10, padx=20
        ).pack(pady=10)

        self.progresso = ttk.Progressbar(frame, mode="indeterminate", length=400)
        self.progresso.pack(pady=3)

        # ── Correção manual ──────────────────────
        grp3 = ttk.LabelFrame(frame, text="Dimensões Extraídas — corrija se necessário")
        grp3.pack(fill="both", expand=True, padx=10, pady=8)

        frame_campos = tk.Frame(grp3)
        frame_campos.pack(fill="x", padx=5, pady=5)

        campos_edit = [
            ("Código da Peça:",   "edit_codigo"),
            ("Ø Externo (mm):",   "edit_diam_ext"),
            ("Ø Interno (mm):",   "edit_diam_int"),
            ("Comprimento (mm):", "edit_comp"),
            ("Peso kg (0=auto):", "edit_peso"),
        ]

        for i, (label, key) in enumerate(campos_edit):
            col = (i % 2) * 3
            row = i // 2
            tk.Label(frame_campos, text=label,
                     font=("Helvetica", 9), anchor="e", width=18
                     ).grid(row=row, column=col, padx=5, pady=3, sticky="e")
            var = tk.StringVar(value="")
            self.vars_edit[key] = var
            tk.Entry(frame_campos, textvariable=var, width=14
                     ).grid(row=row, column=col+1, padx=5, pady=3, sticky="w")

        tk.Button(
            grp3,
            text="✔  Aplicar Correções e Recalcular",
            command=self._aplicar_correcoes,
            bg="#e67e22", fg="white",
            font=("Helvetica", 9, "bold"),
            relief="flat", padx=10, pady=4
        ).pack(pady=4)

        self.txt_dims = scrolledtext.ScrolledText(
            grp3, height=6, font=("Courier", 9),
            state="disabled", bg="#f8f9fa"
        )
        self.txt_dims.pack(fill="both", expand=True, padx=5, pady=5)

    def _aba_parametros(self):
        frame = self.aba_params
        campos = [
            ("Custo hora Torno CNC (R$/h):", "custo_hora_torno_cnc", "85.0"),
            ("Custo hora Fresa CNC (R$/h):", "custo_hora_fresa_cnc", "95.0"),
            ("Custo material bruto (R$/kg):", "custo_material_kg",    "8.50"),
            ("Overhead (%):",                 "overhead_percentual",  "25.0"),
            ("Lucro desejado (%):",           "lucro_percentual",     "15.0"),
            ("Tempo de setup (min):",         "tempo_setup_min",      "30.0"),
            ("Qtde no lote:",                 "qtde_lote",            "1"),
            ("Máquina:",                      "maquina",              "CNC TORNO"),
            ("Cliente:",                      "cliente",              ""),
            ("Número do orçamento:",          "numero_orcamento",     ""),
        ]
        self.vars_params = {}
        for i, (label, attr, default) in enumerate(campos):
            tk.Label(frame, text=label,
                     font=("Helvetica", 9), anchor="e"
                     ).grid(row=i, column=0, padx=10, pady=4, sticky="e")
            var = tk.StringVar(value=default)
            self.vars_params[attr] = var
            tk.Entry(frame, textvariable=var, width=20
                     ).grid(row=i, column=1, padx=10, pady=4, sticky="w")

        tk.Button(
            frame, text="✔  Aplicar Parâmetros",
            command=self._aplicar_parametros,
            bg="#27ae60", fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat", padx=10, pady=5
        ).grid(row=len(campos), column=0, columnspan=2, pady=15)

    def _aba_resultados(self):
        frame = self.aba_result
        self.txt_resultado = scrolledtext.ScrolledText(
            frame, font=("Courier", 10),
            state="disabled", bg="#f8f9fa"
        )
        self.txt_resultado.pack(fill="both", expand=True, padx=5, pady=5)

        tk.Button(
            frame,
            text="📄   GERAR RELATÓRIO PDF",
            command=self._gerar_pdf,
            bg="#e74c3c", fg="white",
            font=("Helvetica", 12, "bold"),
            relief="flat", pady=8, padx=20
        ).pack(pady=10)

    def _aba_log(self):
        self.txt_log = scrolledtext.ScrolledText(
            self.aba_log, font=("Courier", 8),
            state="disabled", bg="#1e1e1e", fg="#00ff41"
        )
        self.txt_log.pack(fill="both", expand=True)

    # ── Ações ────────────────────────────────────

    def _selecionar_desenho(self):
        caminho = filedialog.askopenfilename(
            title="Selecione o desenho técnico",
            filetypes=[
                ("Arquivos suportados", "*.pdf *.jpg *.jpeg *.png"),
                ("PDF", "*.pdf"),
                ("Imagens", "*.jpg *.jpeg *.png"),
            ]
        )
        if caminho:
            self.caminho_desenho.set(caminho)
            self.log(f"Desenho selecionado: {caminho}")

    def _selecionar_planilha(self):
        caminho = filedialog.askopenfilename(
            title="Selecione a planilha de custos",
            filetypes=[("Excel", "*.xlsx *.xls")]
        )
        if caminho:
            self.caminho_planilha.set(caminho)
            self.log(f"Planilha selecionada: {caminho}")

    def _aplicar_correcoes(self):
        if not self.dims_resultado:
            messagebox.showwarning("Atenção", "Processe um desenho primeiro.")
            return
        try:
            cod  = self.vars_edit["edit_codigo"].get().strip()
            ext  = self.vars_edit["edit_diam_ext"].get().strip()
            int_ = self.vars_edit["edit_diam_int"].get().strip()
            comp = self.vars_edit["edit_comp"].get().strip()
            peso = self.vars_edit["edit_peso"].get().strip()

            if cod:  self.dims_resultado.codigo_peca = cod
            if ext:  self.dims_resultado.diametro_externo_mm = float(ext)
            if int_: self.dims_resultado.diametro_interno_mm = float(int_)
            if comp: self.dims_resultado.comprimento_mm = float(comp)
            if peso: self.dims_resultado.peso_kg = float(peso)

            self.resultado_calculo = calcular(self.dims_resultado, self.params_custo)
            resumo_c = resumo_calculo(self.resultado_calculo)
            self._atualizar_txt(self.txt_resultado, resumo_c)
            self.notebook.select(2)
            self.status_var.set(
                f"✅ Recalculado! Custo total: R$ {self.resultado_calculo.custo_total:.2f}"
            )
            self.log("Dimensões corrigidas e recalculadas.")
        except ValueError as e:
            messagebox.showerror("Erro", f"Valor inválido: {e}")

    def _aplicar_parametros(self):
        try:
            self.params_custo.custo_hora_torno_cnc = float(self.vars_params["custo_hora_torno_cnc"].get())
            self.params_custo.custo_hora_fresa_cnc = float(self.vars_params["custo_hora_fresa_cnc"].get())
            self.params_custo.custo_material_kg    = float(self.vars_params["custo_material_kg"].get())
            self.params_custo.overhead_percentual  = float(self.vars_params["overhead_percentual"].get())
            self.params_custo.lucro_percentual      = float(self.vars_params["lucro_percentual"].get())
            self.params_custo.tempo_setup_min       = float(self.vars_params["tempo_setup_min"].get())
            self.params_custo.qtde_lote             = int(self.vars_params["qtde_lote"].get())
            self.params_custo.maquina               = self.vars_params["maquina"].get()
            self.params_custo.cliente               = self.vars_params["cliente"].get()
            self.params_custo.numero_orcamento      = self.vars_params["numero_orcamento"].get()
            messagebox.showinfo("OK", "Parâmetros aplicados com sucesso!")
            self.log("Parâmetros de custo atualizados.")
        except ValueError as e:
            messagebox.showerror("Erro", f"Valor inválido: {e}")

    def _processar(self):
        if not self.caminho_desenho.get():
            messagebox.showwarning("Atenção", "Selecione um desenho técnico.")
            return
        self.progresso.start(10)
        self.status_var.set("Processando... aguarde.")
        thread = threading.Thread(target=self._processar_thread, daemon=True)
        thread.start()

    def _processar_thread(self):
        try:
            self.log("Iniciando leitura do arquivo...")
            imagens, texto_ocr = ler_arquivo(self.caminho_desenho.get())
            self.log(f"OCR concluído. {len(texto_ocr)} caracteres extraídos.")

            self.log("\nExtraindo dimensões...")
            self.dims_resultado = extrair_dimensoes(texto_ocr)
            resumo = resumo_dimensoes(self.dims_resultado)
            self.log(resumo)
            self._atualizar_txt(self.txt_dims, resumo)

            # Preenche campos de correção com o que foi extraído
            self.root.after(0, self._preencher_campos_edicao)

            if self.caminho_planilha.get():
                self.log("\nLendo planilha de custos...")
                params_xlsx = ler_planilha_custos(
                    self.caminho_planilha.get(),
                    self.dims_resultado.codigo_peca
                )
                if params_xlsx.cliente:
                    self.params_custo.cliente = params_xlsx.cliente

            self.log("\nCalculando...")
            self.resultado_calculo = calcular(self.dims_resultado, self.params_custo)
            resumo_c = resumo_calculo(self.resultado_calculo)
            self.log(resumo_c)
            self._atualizar_txt(self.txt_resultado, resumo_c)

            self.root.after(0, lambda: self.notebook.select(2))
            self.root.after(0, lambda: self.status_var.set(
                f"✅ Concluído! Custo total: R$ {self.resultado_calculo.custo_total:.2f}"
            ))

        except Exception as e:
            self.log(f"❌ ERRO: {e}")
            self.root.after(0, lambda: messagebox.showerror("Erro", str(e)))
            self.root.after(0, lambda: self.status_var.set(f"Erro: {e}"))
        finally:
            self.root.after(0, self.progresso.stop)

    def _preencher_campos_edicao(self):
        """Preenche os campos de correção com os valores extraídos pelo OCR."""
        if not self.dims_resultado:
            return
        self.vars_edit["edit_codigo"].set(self.dims_resultado.codigo_peca)
        self.vars_edit["edit_diam_ext"].set(
            f"{self.dims_resultado.diametro_externo_mm:.2f}"
            if self.dims_resultado.diametro_externo_mm > 0 else ""
        )
        self.vars_edit["edit_diam_int"].set(
            f"{self.dims_resultado.diametro_interno_mm:.2f}"
            if self.dims_resultado.diametro_interno_mm > 0 else ""
        )
        self.vars_edit["edit_comp"].set(
            f"{self.dims_resultado.comprimento_mm:.2f}"
            if self.dims_resultado.comprimento_mm > 0 else ""
        )
        self.vars_edit["edit_peso"].set(
            f"{self.dims_resultado.peso_kg:.3f}"
            if self.dims_resultado.peso_kg > 0 else ""
        )

    def _gerar_pdf(self):
        if not self.resultado_calculo:
            messagebox.showwarning("Atenção", "Processe um desenho antes de gerar o relatório.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar relatório PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=(
                f"orcamento_{self.dims_resultado.codigo_peca}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            )
        )
        if not caminho:
            return

        try:
            self.status_var.set("Gerando PDF...")
            gerar_relatorio(self.dims_resultado, self.params_custo,
                            self.resultado_calculo, caminho)
            self.status_var.set(f"✅ Relatório salvo: {caminho}")
            messagebox.showinfo("Sucesso!", f"Relatório gerado:\n{caminho}")
            os.startfile(caminho)
            self.log(f"PDF gerado: {caminho}")
        except Exception as e:
            messagebox.showerror("Erro ao gerar PDF", str(e))
            self.log(f"❌ Erro PDF: {e}")

    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.root.after(0, self._append_log, f"[{ts}] {msg}\n")

    def _append_log(self, linha: str):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", linha)
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def _atualizar_txt(self, widget, texto: str):
        self.root.after(0, self._set_txt, widget, texto)

    def _set_txt(self, widget, texto: str):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", texto)
        widget.configure(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = AppOrcamento(root)
    root.mainloop()