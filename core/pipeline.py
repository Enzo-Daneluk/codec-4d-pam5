"""
Pipeline completo de codificação/decodificação.

Implementa a sequência de apresentação exigida nas normas:

HOST A (envio):
    1. digitar o texto
    2. aplicar o algoritmo de criptografia
    3. transformação em binário (ASCII estendido)
    4. aplicar o princípio do algoritmo de codificação de linha (4D-PAM5)
    5. apresentação do gráfico
    6. envio para o outro lado

HOST B (recepção):
    1. recepção
    2. apresentar o gráfico
    3. aplicar o algoritmo de codificação de linha de modo inverso
    4. transformação de binário para ASCII
    5. aplicar o algoritmo de criptografia inverso
    6. mostra a mensagem
"""

from dataclasses import dataclass
from typing import List

from crypto import encrypt, decrypt
from conversao import texto_para_binario, binario_para_texto
from codec_4dpam5 import codificar, decodificar


@dataclass
class ResultadoCodificacaoHostA:
    """Armazena todos os estágios intermediários do lado do transmissor (T1 pede para exibir cada um)."""
    texto_original: str
    texto_criptografado: str
    binario: str
    canais_pam5: List[List[int]]
    tamanho_bits_original: int


@dataclass
class ResultadoDecodificacaoHostB:
    """Armazena todos os estágios intermediários do lado do receptor."""
    canais_pam5_recebidos: List[List[int]]
    binario_recuperado: str
    texto_criptografado_recuperado: str
    texto_final: str


def processar_envio(texto: str, chave_cripto: str) -> ResultadoCodificacaoHostA:
    """Executa todo o pipeline do Host A, retornando cada estágio para exibição na GUI (T1)."""
    texto_cripto = encrypt(texto, chave_cripto)
    binario = texto_para_binario(texto_cripto)
    canais = codificar(binario)

    return ResultadoCodificacaoHostA(
        texto_original=texto,
        texto_criptografado=texto_cripto,
        binario=binario,
        canais_pam5=canais,
        tamanho_bits_original=len(binario),
    )


def processar_recepcao(
    canais_recebidos: List[List[int]],
    tamanho_bits_original: int,
    chave_cripto: str,
) -> ResultadoDecodificacaoHostB:
    """Executa todo o pipeline do Host B (processo inverso), a partir dos dados recebidos pela rede."""
    binario = decodificar(canais_recebidos, tamanho_bits_original)
    texto_cripto_recuperado = binario_para_texto(binario)
    texto_final = decrypt(texto_cripto_recuperado, chave_cripto)

    return ResultadoDecodificacaoHostB(
        canais_pam5_recebidos=canais_recebidos,
        binario_recuperado=binario,
        texto_criptografado_recuperado=texto_cripto_recuperado,
        texto_final=texto_final,
    )


if __name__ == "__main__":
    CHAVE = "UTFPR2026"
    mensagem = "Olá! Codificação de linha é incrível? Sim!"

    print("=" * 60)
    print("HOST A — ENVIO")
    print("=" * 60)
    resultado_a = processar_envio(mensagem, CHAVE)
    print(f"1. Texto digitado      : {resultado_a.texto_original!r}")
    print(f"2. Texto criptografado : {resultado_a.texto_criptografado!r}")
    print(f"3. Binário ({len(resultado_a.binario)} bits) : {resultado_a.binario[:64]}...")
    print(f"4. Canais PAM5 (Par A) : {resultado_a.canais_pam5[0][:15]}...")

    # Simula o "envio pela rede": na prática, isso seria serializado
    # (ex: JSON) e enviado via socket -- ver módulo network/.
    canais_recebidos = resultado_a.canais_pam5
    tamanho_recebido = resultado_a.tamanho_bits_original

    print("\n" + "=" * 60)
    print("HOST B — RECEPÇÃO")
    print("=" * 60)
    resultado_b = processar_recepcao(canais_recebidos, tamanho_recebido, CHAVE)
    print(f"3. Codificação inversa -> binário ({len(resultado_b.binario_recuperado)} bits)")
    print(f"4. Binário -> ASCII    : {resultado_b.texto_criptografado_recuperado!r}")
    print(f"5. Criptografia inversa: {resultado_b.texto_final!r}")

    print("\n" + "=" * 60)
    print(f"RESULTADO: {'SUCESSO' if mensagem == resultado_b.texto_final else 'FALHOU'}")
    print("=" * 60)
