# Codificação de linha 4D-PAM5

Projeto acadêmico da disciplina de Redes de Computadores (UTFPR).

Implementa a codificação 4D-PAM5, usada no 1000BASE-T (Gigabit Ethernet), em um sistema de dois hosts: o Host A cifra o texto, converte para binário, codifica em 4D-PAM5 e envia por TCP; o Host B recebe, decodifica e recupera a mensagem original. A interface mostra a forma de onda dos quatro pares em cada etapa.

## Como funciona a codificação

Cada byte é dividido em quatro grupos de 2 bits. Cada grupo vai para um dos quatro pares do cabo e é mapeado para um dos níveis `-2, -1, +1, +2`. O decodificador faz o caminho inverso e o pipeline foi testado com texto acentuado (ç, ã, é) usando ASCII estendido.

## Estrutura

```
core/
  crypto.py         cifra XOR com chave
  conversao.py      texto <-> binário (ASCII estendido)
  codec_4dpam5.py   codificador e decodificador 4D-PAM5
  pipeline.py       junta as etapas de envio e recepção
network/
  network.py        servidor (Host B) e cliente (Host A) TCP
gui/
  plotagem.py       gráficos das formas de onda
  app.py            interface Tkinter (ponto de entrada)
```

## Tecnologias

Python 3.9+, Tkinter, matplotlib e sockets TCP.

## Como executar

```bash
pip install matplotlib
cd gui
python app.py
```

Para testar em uma máquina só, abra duas instâncias: na aba "Host B" de uma, clique em "Aguardar conexão"; na aba "Host A" da outra, use o IP `127.0.0.1` e a mesma porta. Em duas máquinas, use o IP local do Host B (mostrado na interface).

Cada módulo de `core/` e `network/` tem testes no bloco `if __name__ == "__main__":`

```bash
cd core
python crypto.py && python conversao.py && python codec_4dpam5.py && python pipeline.py
```
