"""
Módulo de conversão Texto <-> Binário usando ASCII estendido (Latin-1 / CP-1252).

Usamos Latin-1 (ISO-8859-1) como tabela ASCII estendida porque:
- Mapeia diretamente 1 caractere = 1 byte (0-255), sem ambiguidade.
- Cobre letras acentuadas e caracteres especiais do português
  (á, ã, â, à, ç, é, ê, í, ó, ô, õ, ú, ü, etc.)

Isso atende ao requisito T5 das normas do trabalho.
"""

BITS_POR_CARACTERE = 8


def texto_para_binario(texto: str) -> str:
    """
    Converte uma string em uma sequência binária contínua,
    usando 8 bits por caractere (ASCII estendido / Latin-1).

    Exemplo: "A" -> "01000001"
             "á" -> "11100001"
    """
    bits = []
    for ch in texto:
        valor = ord(ch)
        if valor > 255:
            raise ValueError(
                f"Caractere {ch!r} (codepoint {valor}) está fora da faixa "
                f"do ASCII estendido (0-255)."
            )
        byte_bin = format(valor, "08b")
        bits.append(byte_bin)
    return "".join(bits)


def binario_para_texto(binario: str) -> str:
    """
    Converte uma sequência binária (múltiplo de 8 bits) de volta
    para texto, usando ASCII estendido / Latin-1.
    """
    if len(binario) % BITS_POR_CARACTERE != 0:
        raise ValueError(
            f"Sequência binária com tamanho inválido ({len(binario)} bits). "
            f"Deve ser múltiplo de {BITS_POR_CARACTERE}."
        )

    caracteres = []
    for i in range(0, len(binario), BITS_POR_CARACTERE):
        byte_str = binario[i:i + BITS_POR_CARACTERE]
        valor = int(byte_str, 2)
        caracteres.append(chr(valor))

    return "".join(caracteres)


if __name__ == "__main__":
    texto = "Ação Café"
    binario = texto_para_binario(texto)
    de_volta = binario_para_texto(binario)

    print(f"Texto     : {texto!r}")
    print(f"Binário   : {binario}")
    print(f"Nº de bits: {len(binario)}  (esperado: {len(texto) * 8})")
    print(f"De volta  : {de_volta!r}")
    print(f"Bate? {texto == de_volta}")
