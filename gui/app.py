"""
Aplicação principal - GUI em Tkinter.

Atende ao requisito T1 das normas:
  - Mostra: msg escrita, msg criptografada, msg em binário,
    msg aplicado o algoritmo e o gráfico.

A janela tem duas abas: "Host A (Enviar)" e "Host B (Receber)",
já que o mesmo programa deve funcionar nos dois papéis (basta
rodar a aplicação em duas máquinas diferentes e escolher o papel).
"""

import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# Permite importar os módulos de core/ e network/ a partir daqui
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "network"))

from pipeline import processar_envio, processar_recepcao
from network import ServidorHostB, ClienteHostA, obter_ip_local, PORTA_PADRAO

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from plotagem import criar_figura_pam5

CHAVE_CRIPTO_PADRAO = "UTFPR2026"


class AplicacaoPrincipal(tk.Tk):
    """Janela principal da aplicação, com abas para Host A e Host B."""

    def __init__(self):
        super().__init__()
        self.title("Codificação de Linha 4D-PAM5 — UTFPR")
        self.geometry("1000x800")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.aba_envio = AbaHostA(self.notebook)
        self.aba_recepcao = AbaHostB(self.notebook)

        self.notebook.add(self.aba_envio, text="Host A — Enviar")
        self.notebook.add(self.aba_recepcao, text="Host B — Receber")


class AbaHostA(ttk.Frame):
    """
    Aba do transmissor.

    Fluxo (conforme normas):
        digitar texto -> criptografar -> binário -> 4D-PAM5 -> gráfico -> enviar
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.canais_atuais = None
        self.tamanho_bits_atual = None
        self._montar_widgets()

    def _montar_widgets(self):
        # --- Bloco de entrada ---
        frame_entrada = ttk.LabelFrame(self, text="1. Mensagem")
        frame_entrada.pack(fill="x", padx=8, pady=4)

        ttk.Label(frame_entrada, text="Texto a enviar:").pack(anchor="w", padx=4)
        self.entry_texto = ttk.Entry(frame_entrada, width=80)
        self.entry_texto.pack(fill="x", padx=4, pady=2)
        self.entry_texto.insert(0, "Olá, mundo! Codificação de linha.")

        frame_chave = ttk.Frame(frame_entrada)
        frame_chave.pack(fill="x", padx=4, pady=2)
        ttk.Label(frame_chave, text="Chave de criptografia:").pack(side="left")
        self.entry_chave = ttk.Entry(frame_chave, width=30)
        self.entry_chave.pack(side="left", padx=4)
        self.entry_chave.insert(0, CHAVE_CRIPTO_PADRAO)

        ttk.Button(
            frame_entrada, text="Processar (criptografar + codificar)",
            command=self._processar
        ).pack(pady=4)

        # --- Bloco de estágios intermediários (exigido em T1) ---
        frame_estagios = ttk.LabelFrame(self, text="2. Estágios do processamento")
        frame_estagios.pack(fill="x", padx=8, pady=4)

        self.txt_criptografado = self._criar_campo_somente_leitura(frame_estagios, "Mensagem criptografada:")
        self.txt_binario = self._criar_campo_somente_leitura(frame_estagios, "Mensagem em binário:")
        self.txt_pam5 = self._criar_campo_somente_leitura(frame_estagios, "Níveis 4D-PAM5 (por par, resumido):")

        # --- Bloco do gráfico ---
        frame_grafico = ttk.LabelFrame(self, text="3. Forma de onda (gráfico)")
        frame_grafico.pack(fill="both", expand=True, padx=8, pady=4)
        self.frame_canvas_grafico = frame_grafico
        self.canvas_grafico = None

        # --- Bloco de rede ---
        frame_rede = ttk.LabelFrame(self, text="4. Envio pela rede")
        frame_rede.pack(fill="x", padx=8, pady=4)

        ttk.Label(frame_rede, text=f"Seu IP local: {obter_ip_local()}").pack(anchor="w", padx=4)

        frame_destino = ttk.Frame(frame_rede)
        frame_destino.pack(fill="x", padx=4, pady=2)
        ttk.Label(frame_destino, text="IP do Host B (destino):").pack(side="left")
        self.entry_ip_destino = ttk.Entry(frame_destino, width=20)
        self.entry_ip_destino.pack(side="left", padx=4)
        self.entry_ip_destino.insert(0, "192.168.0.X")

        ttk.Label(frame_destino, text="Porta:").pack(side="left", padx=(12, 0))
        self.entry_porta = ttk.Entry(frame_destino, width=8)
        self.entry_porta.pack(side="left", padx=4)
        self.entry_porta.insert(0, str(PORTA_PADRAO))

        self.btn_enviar = ttk.Button(
            frame_rede, text="Enviar para o Host B", command=self._enviar, state="disabled"
        )
        self.btn_enviar.pack(pady=4)

        self.label_status = ttk.Label(frame_rede, text="", foreground="blue")
        self.label_status.pack(anchor="w", padx=4)

    def _criar_campo_somente_leitura(self, parent, rotulo: str) -> tk.Text:
        ttk.Label(parent, text=rotulo).pack(anchor="w", padx=4)
        campo = tk.Text(parent, height=2, wrap="char")
        campo.pack(fill="x", padx=4, pady=2)
        campo.configure(state="disabled")
        return campo

    def _atualizar_campo(self, campo: tk.Text, valor: str):
        campo.configure(state="normal")
        campo.delete("1.0", "end")
        campo.insert("1.0", valor)
        campo.configure(state="disabled")

    def _processar(self):
        """Executa o pipeline completo do Host A e atualiza a interface (T1, T5, T6)."""
        texto = self.entry_texto.get()
        chave = self.entry_chave.get()

        if not texto:
            messagebox.showwarning("Atenção", "Digite uma mensagem.")
            return
        if not chave:
            messagebox.showwarning("Atenção", "Informe a chave de criptografia.")
            return

        try:
            resultado = processar_envio(texto, chave)
        except Exception as e:
            messagebox.showerror("Erro ao processar", str(e))
            return

        self._atualizar_campo(self.txt_criptografado, repr(resultado.texto_criptografado))
        self._atualizar_campo(self.txt_binario, resultado.binario)

        resumo_pam5 = "\n".join(
            f"Par {chr(65+i)}: {canal[:20]}{' ...' if len(canal) > 20 else ''}"
            for i, canal in enumerate(resultado.canais_pam5)
        )
        self._atualizar_campo(self.txt_pam5, resumo_pam5)

        self._atualizar_grafico(resultado.canais_pam5, titulo="Host A — Sinal a ser enviado")

        self.canais_atuais = resultado.canais_pam5
        self.tamanho_bits_atual = resultado.tamanho_bits_original
        self.btn_enviar.configure(state="normal")
        self.label_status.configure(text="Processamento concluído. Pronto para enviar.")

    def _atualizar_grafico(self, canais, titulo: str):
        if self.canvas_grafico is not None:
            self.canvas_grafico.get_tk_widget().destroy()

        fig = criar_figura_pam5(canais, titulo=titulo)
        self.canvas_grafico = FigureCanvasTkAgg(fig, master=self.frame_canvas_grafico)
        self.canvas_grafico.draw()
        self.canvas_grafico.get_tk_widget().pack(fill="both", expand=True)

    def _enviar(self):
        """Envia os dados codificados para o Host B via rede (T3, T7)."""
        if self.canais_atuais is None:
            return

        ip_destino = self.entry_ip_destino.get().strip()
        try:
            porta = int(self.entry_porta.get().strip())
        except ValueError:
            messagebox.showerror("Erro", "Porta inválida.")
            return

        def tarefa_envio():
            try:
                cliente = ClienteHostA(ip_destino, porta)
                cliente.enviar(self.canais_atuais, self.tamanho_bits_atual)
                self.label_status.configure(text=f"Enviado com sucesso para {ip_destino}:{porta}!")
            except Exception as e:
                self.label_status.configure(text=f"Erro ao enviar: {e}")

        # Roda em thread separada para não congelar a GUI durante a conexão
        threading.Thread(target=tarefa_envio, daemon=True).start()


class AbaHostB(ttk.Frame):
    """
    Aba do receptor.

    Fluxo (conforme normas):
        recepção -> gráfico -> codificação inversa -> binário->ASCII -> criptografia inversa -> mensagem
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.servidor = None
        self.canvas_grafico = None
        self._montar_widgets()

    def _montar_widgets(self):
        frame_config = ttk.LabelFrame(self, text="1. Configuração de recepção")
        frame_config.pack(fill="x", padx=8, pady=4)

        ttk.Label(frame_config, text=f"Seu IP local: {obter_ip_local()}").pack(anchor="w", padx=4)

        frame_porta = ttk.Frame(frame_config)
        frame_porta.pack(fill="x", padx=4, pady=2)
        ttk.Label(frame_porta, text="Porta de escuta:").pack(side="left")
        self.entry_porta = ttk.Entry(frame_porta, width=8)
        self.entry_porta.pack(side="left", padx=4)
        self.entry_porta.insert(0, str(PORTA_PADRAO))

        ttk.Label(frame_porta, text="Chave de criptografia:").pack(side="left", padx=(12, 0))
        self.entry_chave = ttk.Entry(frame_porta, width=30)
        self.entry_chave.pack(side="left", padx=4)
        self.entry_chave.insert(0, CHAVE_CRIPTO_PADRAO)

        self.btn_escutar = ttk.Button(
            frame_config, text="Aguardar conexão (escutar)", command=self._iniciar_escuta
        )
        self.btn_escutar.pack(pady=4)

        self.label_status = ttk.Label(frame_config, text="Aguardando início...", foreground="blue")
        self.label_status.pack(anchor="w", padx=4)

        frame_grafico = ttk.LabelFrame(self, text="2. Forma de onda recebida")
        frame_grafico.pack(fill="both", expand=True, padx=8, pady=4)
        self.frame_canvas_grafico = frame_grafico

        frame_estagios = ttk.LabelFrame(self, text="3. Decodificação")
        frame_estagios.pack(fill="x", padx=8, pady=4)

        self.txt_binario = self._criar_campo_somente_leitura(frame_estagios, "Binário recuperado:")
        self.txt_criptografado = self._criar_campo_somente_leitura(frame_estagios, "ASCII (ainda criptografado):")
        self.txt_final = self._criar_campo_somente_leitura(frame_estagios, "Mensagem final (decifrada):")

    def _criar_campo_somente_leitura(self, parent, rotulo: str) -> tk.Text:
        ttk.Label(parent, text=rotulo).pack(anchor="w", padx=4)
        campo = tk.Text(parent, height=2, wrap="char")
        campo.pack(fill="x", padx=4, pady=2)
        campo.configure(state="disabled")
        return campo

    def _atualizar_campo(self, campo: tk.Text, valor: str):
        campo.configure(state="normal")
        campo.delete("1.0", "end")
        campo.insert("1.0", valor)
        campo.configure(state="disabled")

    def _iniciar_escuta(self):
        try:
            porta = int(self.entry_porta.get().strip())
        except ValueError:
            messagebox.showerror("Erro", "Porta inválida.")
            return

        self.btn_escutar.configure(state="disabled")
        self.label_status.configure(text=f"Escutando na porta {porta}... (aguardando Host A)")

        def callback(canais, tamanho_bits):
            # Esse callback roda na thread do servidor; agenda atualização da GUI na thread principal
            self.after(0, lambda: self._processar_recebido(canais, tamanho_bits))

        def tarefa_servidor():
            self.servidor = ServidorHostB(porta=porta, callback=callback)
            try:
                self.servidor.iniciar()
            except Exception as e:
                self.after(0, lambda: self.label_status.configure(text=f"Erro: {e}"))

        threading.Thread(target=tarefa_servidor, daemon=True).start()

    def _processar_recebido(self, canais, tamanho_bits):
        self.label_status.configure(text="Dados recebidos! Decodificando...")
        self._atualizar_grafico(canais, titulo="Host B — Sinal recebido")

        chave = self.entry_chave.get()
        try:
            resultado = processar_recepcao(canais, tamanho_bits, chave)
        except Exception as e:
            messagebox.showerror("Erro ao decodificar", str(e))
            return

        self._atualizar_campo(self.txt_binario, resultado.binario_recuperado)
        self._atualizar_campo(self.txt_criptografado, repr(resultado.texto_criptografado_recuperado))
        self._atualizar_campo(self.txt_final, resultado.texto_final)

        self.label_status.configure(text="Mensagem decodificada com sucesso!")
        self.btn_escutar.configure(state="normal")

    def _atualizar_grafico(self, canais, titulo: str):
        if self.canvas_grafico is not None:
            self.canvas_grafico.get_tk_widget().destroy()

        fig = criar_figura_pam5(canais, titulo=titulo)
        self.canvas_grafico = FigureCanvasTkAgg(fig, master=self.frame_canvas_grafico)
        self.canvas_grafico.draw()
        self.canvas_grafico.get_tk_widget().pack(fill="both", expand=True)


if __name__ == "__main__":
    app = AplicacaoPrincipal()
    app.mainloop()
