import socket
import time

HOST = '127.0.0.1'
PORT = 5000
TAMANHO_PACOTE = 3
WINDOW_SIZE = 4

def calcular_checksum(seq_num, payload):
    soma = seq_num + sum(ord(c) for c in payload)
    return soma % 256

def criar_pacote(seq_num, payload):
    checksum = calcular_checksum(seq_num, payload)
    return f"{seq_num}|{payload}|{checksum}"

def quebrar_mensagem(msg, limite):
    msg = msg[:limite]  # Garante o limite máximo da mensagem
    pacotes = []
    for i in range(0, len(msg), TAMANHO_PACOTE):
        payload = msg[i:i + TAMANHO_PACOTE]
        pacotes.append((i // TAMANHO_PACOTE, payload))
    return pacotes

def cliente():
    protocolo = input("Escolha o protocolo (1 - Go-Back-N, 2 - Repetição Seletiva): ")
    modo = "GBN" if protocolo == "1" else "SR"

    tamanho_msg = int(input("Digite o tamanho máximo da mensagem: "))
    mensagem = input("Digite a mensagem a ser enviada: ")

    pacotes = quebrar_mensagem(mensagem, tamanho_msg)
    total_pacotes = len(pacotes)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall((modo + "\n").encode())  # Envia o modo com quebra de linha

        print(f"\n[Cliente] Modo: {modo} | Janela: {WINDOW_SIZE} | Total de pacotes: {total_pacotes}\n")

        base = 0
        next_seq = 0
        acked = [False] * total_pacotes
        tempos_envio = {}
        ack_recebido = set()  # Conjunto para controlar ACKs já recebidos

        while base < total_pacotes:
            # Envia os pacotes dentro da janela
            while next_seq < base + WINDOW_SIZE and next_seq < total_pacotes:
                pacote = criar_pacote(*pacotes[next_seq])
                tempos_envio[next_seq] = time.time()
                s.sendall((pacote + "\n").encode())
                print(f"[Cliente] ➡️ Enviado pacote {next_seq}: {pacote}")
                next_seq += 1

            # Aguarda ACKs
            resposta_buffer = ""
            while not "\n" in resposta_buffer:
                dados = s.recv(1024)
                if not dados:
                    break
                resposta_buffer += dados.decode()

            respostas = resposta_buffer.strip().split("\n")
            for resposta in respostas:
                partes = resposta.strip().split("|")
                if len(partes) != 2:
                    print(f"[Cliente] ❌ ACK inválido recebido: {resposta}")
                    continue

                tipo, ack_seq = partes
                ack_seq = int(ack_seq)

                # Evita imprimir ACKs duplicados
                if ack_seq in ack_recebido:
                    continue
                ack_recebido.add(ack_seq)

                rtt = time.time() - tempos_envio[ack_seq]
                print(f"[Cliente] ⬅️ ACK recebido do pacote {ack_seq} | RTT: {rtt:.3f}s")

                acked[ack_seq] = True
                if modo == "GBN":
                    if ack_seq == base:
                        while base < total_pacotes and acked[base]:
                            base += 1
                else:  # SR
                    # Aceita qualquer ACK, mesmo que fora de ordem
                    if ack_seq < total_pacotes:
                        acked[ack_seq] = True  # Marca o pacote como confirmado

                    # Move a base da janela quando os pacotes anteriores foram confirmados
                    while base < total_pacotes and acked[base]:
                        base += 1

        print("\n[Cliente] ✅ Comunicação finalizada.")

if __name__ == "__main__":
    cliente()
