"""
Módulo de plotagem das formas de onda 4D-PAM5 (T2 das normas).

Gera um gráfico com 4 subplots (um por canal/par/dimensão), no estilo
"degrau" (step), que é a forma correta de representar PAM, já que o
nível de tensão se mantém constante durante cada intervalo de símbolo.
"""

import matplotlib
matplotlib.use("Agg")  # backend sem display, só para testes fora da GUI
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import List

NOMES_CANAIS = ["Par A", "Par B", "Par C", "Par D"]
CORES_CANAIS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]


def criar_figura_pam5(canais: List[List[int]], titulo: str = "Forma de onda 4D-PAM5") -> Figure:
    """
    Cria uma Figure do matplotlib com 4 subplots (um por canal),
    cada um mostrando o nível PAM5 ao longo do tempo em formato de degrau.

    Essa Figure pode ser embutida em uma janela Tkinter usando
    FigureCanvasTkAgg (ver gui/app.py).
    """
    fig = Figure(figsize=(8, 6), dpi=100)
    fig.suptitle(titulo, fontsize=12, fontweight="bold")

    for idx, (nome, niveis, cor) in enumerate(zip(NOMES_CANAIS, canais, CORES_CANAIS)):
        ax = fig.add_subplot(4, 1, idx + 1)

        # 'step' com where='post' é o jeito correto de representar PAM:
        # o nível se mantém constante até o próximo símbolo.
        eixo_x = list(range(len(niveis) + 1))
        eixo_y = niveis + [niveis[-1]] if niveis else [0]

        ax.step(eixo_x, eixo_y, where="post", color=cor, linewidth=1.5)
        ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
        ax.set_ylim(-2.5, 2.5)
        ax.set_yticks([-2, -1, 0, 1, 2])
        ax.set_ylabel(nome, fontsize=9)
        ax.grid(True, alpha=0.3)

        if idx < len(NOMES_CANAIS) - 1:
            ax.set_xticklabels([])
        else:
            ax.set_xlabel("Símbolo (tempo)", fontsize=9)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    return fig


def salvar_figura_teste(canais: List[List[int]], caminho: str, titulo: str = "Teste") -> None:
    """Função auxiliar só para testar a geração da figura fora da GUI (salva como PNG)."""
    fig = criar_figura_pam5(canais, titulo)
    fig.savefig(caminho)
    plt.close(fig)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "../core")
    from codec_4dpam5 import codificar
    from conversao import texto_para_binario

    texto = "Teste 4D-PAM5!"
    binario = texto_para_binario(texto)
    canais = codificar(binario)

    salvar_figura_teste(canais, "/tmp/teste_pam5.png", titulo=f"Codificação de: {texto!r}")
    print("Figura salva em /tmp/teste_pam5.png")
    print(f"Canais gerados: {[len(c) for c in canais]} símbolos cada")
