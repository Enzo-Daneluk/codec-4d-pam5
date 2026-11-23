"""
Módulo do codec 4D-PAM5 (versão didática, baseada no 1000BASE-T).

CONCEITO:
---------
4D  -> 4 Dimensões: os dados são distribuídos simultaneamente em 4 canais
       (que representam os 4 pares de fios do cabo de par trançado UTP
       Categoria 5e/6 usados no Gigabit Ethernet).
PAM5 -> Pulse Amplitude Modulation de 5 níveis: cada símbolo transmitido
        assume um entre 5 níveis de tensão: -2, -1, 0, +1, +2.

Nesta versão didática, usamos apenas 4 dos 5 níveis (-2,-1,+1,+2) para
codificar diretamente 2 bits por símbolo por canal (4 níveis = 2^2
combinações exatas). O 5º nível (0) é reservado como marcador de
PADDING/fim de quadro, já que no padrão real ele é usado pelo código
trellis de correção de erro (FEC) -- fora do escopo didático deste
trabalho, mas vale mencionar na apresentação como "material extraclasse".

FLUXO:
------
1. A sequência binária é dividida em blocos de 8 bits (1 byte).
2. Cada byte é dividido em 4 grupos de 2 bits.
3. Cada grupo de 2 bits é mapeado para 1 dos 4 pares (canais A, B, C, D).
4. Cada grupo de 2 bits dentro do canal é mapeado para um nível PAM5.
5. O resultado é uma "matriz" de 4 canais x N símbolos.

TABELA DE MAPEAMENTO (2 bits -> nível):
    00 -> -2
    01 -> -1
    10 -> +1
    11 -> +2
"""

from typing import List, Dict

NUM_CANAIS = 4
BITS_POR_NIVEL = 2

MAPA_BITS_PARA_NIVEL: Dict[str, int] = {
    "00": -2,
    "01": -1,
    "10": 1,
    "11": 2,
}

MAPA_NIVEL_PARA_BITS: Dict[int, str] = {v: k for k, v in MAPA_BITS_PARA_NIVEL.items()}

NIVEL_PADDING = 0  # 5º nível do PAM5, usado para preencher bits faltantes


def _completa_multiplo(binario: str, multiplo: int) -> str:
    """Completa a string binária com zeros à direita até ser múltiplo de `multiplo`."""
    resto = len(binario) % multiplo
    if resto == 0:
        return binario
    padding_bits = multiplo - resto
    return binario + ("0" * padding_bits)


def codificar(binario: str) -> List[List[int]]:
    """
    Codifica uma sequência binária no esquema 4D-PAM5.

    Recebe: string de bits, ex: "0100000111100111..."
    Retorna: lista de 4 listas (uma por canal/dimensão), cada uma
             contendo os níveis PAM5 (-2,-1,1,2) ao longo do tempo.

    Exemplo simplificado com 1 byte "01000001":
        Divide em grupos de 2 bits: "01" "00" "00" "01"
        Canal A (par 1) recebe "01" -> nível -1
        Canal B (par 2) recebe "00" -> nível -2
        Canal C (par 3) recebe "00" -> nível -2
        Canal D (par 4) recebe "01" -> nível -1
    """
    bits_por_simbolo_4d = NUM_CANAIS * BITS_POR_NIVEL  # 8 bits por "símbolo 4D"
    binario_completo = _completa_multiplo(binario, bits_por_simbolo_4d)

    canais: List[List[int]] = [[] for _ in range(NUM_CANAIS)]

    for i in range(0, len(binario_completo), bits_por_simbolo_4d):
        bloco = binario_completo[i:i + bits_por_simbolo_4d]
        for canal_idx in range(NUM_CANAIS):
            grupo = bloco[canal_idx * BITS_POR_NIVEL: (canal_idx + 1) * BITS_POR_NIVEL]
            nivel = MAPA_BITS_PARA_NIVEL[grupo]
            canais[canal_idx].append(nivel)

    return canais


def decodificar(canais: List[List[int]], tamanho_bits_original: int = None) -> str:
    """
    Realiza o processo inverso: a partir dos níveis PAM5 nos 4 canais,
    reconstrói a sequência binária original.

    `tamanho_bits_original`: se informado, corta o resultado final no
    tamanho exato (remove o padding de zeros adicionado na codificação).
    Em uma comunicação real, esse valor deve ser enviado junto (ex: em um
    cabeçalho), pois o receptor não tem como saber quantos bits de padding
    foram adicionados.
    """
    num_simbolos = len(canais[0])
    bits_reconstruidos = []

    for simbolo_idx in range(num_simbolos):
        bloco_bits = ""
        for canal_idx in range(NUM_CANAIS):
            nivel = canais[canal_idx][simbolo_idx]
            if nivel == NIVEL_PADDING:
                # Símbolo de padding/preenchimento -> trata como "00"
                bloco_bits += "00"
            else:
                bloco_bits += MAPA_NIVEL_PARA_BITS[nivel]
        bits_reconstruidos.append(bloco_bits)

    binario_completo = "".join(bits_reconstruidos)

    if tamanho_bits_original is not None:
        binario_completo = binario_completo[:tamanho_bits_original]

    return binario_completo


if __name__ == "__main__":
    from conversao import texto_para_binario, binario_para_texto

    texto = "Ação Café"
    binario = texto_para_binario(texto)
    print(f"Texto original : {texto!r}")
    print(f"Binário ({len(binario)} bits): {binario}")

    canais = codificar(binario)
    print("\nCanais PAM5 (4 dimensões):")
    nomes = ["Par A", "Par B", "Par C", "Par D"]
    for nome, c in zip(nomes, canais):
        print(f"  {nome}: {c}")

    binario_recuperado = decodificar(canais, tamanho_bits_original=len(binario))
    texto_recuperado = binario_para_texto(binario_recuperado)

    print(f"\nBinário recuperado: {binario_recuperado}")
    print(f"Texto recuperado  : {texto_recuperado!r}")
    print(f"Bate? {texto == texto_recuperado}")
