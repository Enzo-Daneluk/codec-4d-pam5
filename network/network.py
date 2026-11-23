"""
Módulo de comunicação em rede (T3 e T7 das normas).

Implementa a comunicação via sockets TCP nativos do Python (biblioteca
padrão `socket`), SEM uso de bibliotecas externas de rede -- ou seja,
o mecanismo de comunicação é implementado dentro da própria aplicação,
conforme exigido nas normas ("O mecanismo de comunicação não poderá
ser externo").

PROTOCOLO DE APLICAÇÃO (simples, baseado em JSON + cabeçalho de tamanho):
--------------------------------------------------------------------------
Como TCP é um fluxo de bytes (sem delimitação de mensagens), usamos um
cabeçalho de 4 bytes (inteiro big-endian) indicando o tamanho da mensagem
JSON que vem a seguir. Isso evita problemas de "mensagens coladas" ou
fragmentadas.

Formato do payload (antes de virar JSON):
{
    "canais": [[...], [...], [...], [...]],   # níveis PAM5, 4 canais
    "tamanho_bits_original": 336                # para remover padding no recv
}

IMPORTANTE: os testes devem ser feitos entre duas máquinas reais na rede
(não localhost), conforme exigido nas normas.
"""

import socket
import json
import struct
from typing import List, Tuple, Callable, Optional

PORTA_PADRAO = 5050
TAMANHO_CABECALHO = 4  # bytes, para indicar o tamanho da mensagem


def _enviar_mensagem(conn: socket.socket, dados: dict) -> None:
    """Serializa `dados` em JSON e envia prefixado por um cabeçalho de tamanho."""
    payload = json.dumps(dados).encode("utf-8")
    cabecalho = struct.pack(">I", len(payload))  # 4 bytes, big-endian, unsigned int
    conn.sendall(cabecalho + payload)


def _receber_mensagem(conn: socket.socket) -> dict:
    """Lê o cabeçalho de tamanho e depois lê exatamente esse número de bytes do payload JSON."""
    cabecalho = _recv_exato(conn, TAMANHO_CABECALHO)
    (tamanho_payload,) = struct.unpack(">I", cabecalho)
    payload_bytes = _recv_exato(conn, tamanho_payload)
    return json.loads(payload_bytes.decode("utf-8"))


def _recv_exato(conn: socket.socket, n: int) -> bytes:
    """Garante a leitura de exatamente `n` bytes do socket (TCP pode fragmentar)."""
    dados = b""
    while len(dados) < n:
        pacote = conn.recv(n - len(dados))
        if not pacote:
            raise ConnectionError("Conexão encerrada antes de receber todos os dados.")
        dados += pacote
    return dados


class ServidorHostB:
    """
    Representa o Host B (lado que RECEBE a mensagem).

    Uso típico (dentro da GUI, em uma thread separada para não travar a interface):

        def callback(canais, tamanho_bits):
            resultado = processar_recepcao(canais, tamanho_bits, chave)
            print(resultado.texto_final)

        servidor = ServidorHostB(porta=5050, callback=callback)
        servidor.iniciar()   # bloqueia aguardando 1 conexão
    """

    def __init__(self, porta: int = PORTA_PADRAO,
                 callback: Optional[Callable[[List[List[int]], int], None]] = None):
        self.porta = porta
        self.callback = callback
        self._socket_servidor: Optional[socket.socket] = None

    def iniciar(self) -> None:
        """
        Abre o socket, escuta em todas as interfaces (0.0.0.0) e aguarda
        UMA conexão de cliente. Ao receber dados, chama o callback.

        Bloqueante -- chamar em uma thread separada quando usado com GUI.
        """
        self._socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket_servidor.bind(("0.0.0.0", self.porta))
        self._socket_servidor.listen(1)
        print(f"[Host B] Aguardando conexão na porta {self.porta}...")

        conn, endereco = self._socket_servidor.accept()
        print(f"[Host B] Conexão recebida de {endereco}")

        try:
            dados = _receber_mensagem(conn)
            canais = dados["canais"]
            tamanho_bits = dados["tamanho_bits_original"]
            print(f"[Host B] Dados recebidos ({tamanho_bits} bits originais)")

            if self.callback:
                self.callback(canais, tamanho_bits)
        finally:
            conn.close()

    def parar(self) -> None:
        if self._socket_servidor:
            self._socket_servidor.close()


class ClienteHostA:
    """
    Representa o Host A (lado que ENVIA a mensagem).

    Uso típico:
        cliente = ClienteHostA(ip_destino="192.168.0.42", porta=5050)
        cliente.enviar(canais_pam5, tamanho_bits_original)
    """

    def __init__(self, ip_destino: str, porta: int = PORTA_PADRAO):
        self.ip_destino = ip_destino
        self.porta = porta

    def enviar(self, canais: List[List[int]], tamanho_bits_original: int) -> None:
        """Conecta no Host B e envia os dados codificados em PAM5."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
            print(f"[Host A] Conectando a {self.ip_destino}:{self.porta}...")
            conn.connect((self.ip_destino, self.porta))

            dados = {
                "canais": canais,
                "tamanho_bits_original": tamanho_bits_original,
            }
            _enviar_mensagem(conn, dados)
            print("[Host A] Dados enviados com sucesso.")


def obter_ip_local() -> str:
    """
    Utilitário para descobrir o IP local da máquina na rede
    (útil para exibir na GUI, já que o usuário precisa informar
    esse IP ao parceiro da equipe testando do outro computador).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Não envia pacote de fato; só usa o sistema de rotas do SO
        # para descobrir qual interface seria usada.
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


if __name__ == "__main__":
    print(f"IP local detectado: {obter_ip_local()}")
    print("Para testar manualmente:")
    print("  Terminal 1 (Host B): python3 -c \"from network import *; "
          "ServidorHostB(callback=lambda c,t: print('Recebido!', t, 'bits')).iniciar()\"")
    print("  Terminal 2 (Host A): python3 -c \"from network import *; "
          "ClienteHostA('IP_DO_HOST_B').enviar([[1,-1],[2,-2],[1,1],[-2,2]], 8)\"")
