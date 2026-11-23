"""
Módulo de criptografia.

Implementa uma cifra XOR com chave repetida (stream cipher simples).
Operação simétrica: a mesma função criptografa e descriptografa,
pois XOR aplicado duas vezes com a mesma chave retorna o valor original.

Isso deve ser explicado na apresentação como material extraclasse (T4).
"""

DEFAULT_KEY = "UTFPR2026"


def encrypt(text: str, key: str = DEFAULT_KEY) -> str:
    """
    Criptografa uma string usando XOR byte a byte com uma chave repetida.

    Cada caractere do texto (em seu valor ASCII estendido/Latin-1) é
    combinado via XOR com o caractere correspondente da chave (repetida
    ciclicamente até cobrir todo o texto).

    Retorna uma string onde cada caractere é o resultado do XOR,
    representado como caractere Latin-1 (0-255), preservando o
    tamanho original da mensagem.
    """
    if not key:
        raise ValueError("A chave de criptografia não pode ser vazia.")

    resultado = []
    for i, ch in enumerate(text):
        valor_original = ord(ch)
        valor_chave = ord(key[i % len(key)])
        valor_cifrado = valor_original ^ valor_chave
        # Mantemos dentro da faixa de 1 byte (0-255) para compatibilidade
        # com a tabela ASCII estendido usada depois na conversão p/ binário.
        valor_cifrado = valor_cifrado & 0xFF
        resultado.append(chr(valor_cifrado))

    return "".join(resultado)


def decrypt(cipher_text: str, key: str = DEFAULT_KEY) -> str:
    """
    Descriptografa o texto cifrado pela função encrypt().

    Como XOR é uma operação simétrica (A xor B xor B = A),
    a descriptografia usa exatamente a mesma lógica da criptografia.
    """
    return encrypt(cipher_text, key)


if __name__ == "__main__":
    # Teste rápido do módulo isolado
    msg = "Olá, mundo! Ção ção ção"
    chave = "chave123"

    cifrado = encrypt(msg, chave)
    decifrado = decrypt(cifrado, chave)

    print(f"Original   : {msg!r}")
    print(f"Cifrado    : {cifrado!r}")
    print(f"Decifrado  : {decifrado!r}")
    print(f"Bate? {msg == decifrado}")
