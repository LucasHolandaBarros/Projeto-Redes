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
    payload = payload.ljust(TAMANHO_PACOTE)
    checksum = calcular_checksum(seq_num, payload)
    return f"{seq_num}|{payload}|{checksum}"

def quebrar_mensagem(msg, limite):
    msg = msg[:limite]
    pacotes = []
    for i in range(0, len(msg), TAMANHO_PACOTE):
        payload = msg[i:i + TAMANHO_PACOTE]
        pacotes.append((i // TAMANHO_PACOTE, payload))
    return pacotes

def cliente():
    protocolo = input("Escolha o protocolo (1 - Go-Back-N, 2 - Repetição Seletiva): ")
    modo = "GBN" if protocolo == "1" else "SR"

    tamanho_msg = int(input("Digite o tamanho máximo da mensagem: "))

    if tamanho_msg < TAMANHO_PACOTE:
        tamanho_msg = TAMANHO_PACOTE

    mensagem = input("Digite a mensagem a ser enviada: ")

    pacotes = quebrar_mensagem(mensagem, tamanho_msg)
    total_pacotes = len(pacotes)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.settimeout(2)
        s.sendall((modo + "\n").encode())

        print(f"\n[Cliente] Modo: {modo} | Janela: {WINDOW_SIZE} | Total de pacotes: {total_pacotes}\n")

        base = 0
        next_seq = 0
        acked = [False] * total_pacotes
        tempos_envio = {}
        ack_recebido = set()

        while base < total_pacotes:
            while next_seq < base + WINDOW_SIZE and next_seq < total_pacotes:
                pacote = criar_pacote(*pacotes[next_seq])
                tempos_envio[next_seq] = time.time()
                s.sendall((pacote + "\n").encode())
                print(f"[Cliente] ➡️ Enviado pacote {next_seq}: {pacote}")
                next_seq += 1

            resposta_buffer = ""
            try:
                while "\n" not in resposta_buffer:
                    dados = s.recv(1024)
                    if not dados:
                        break
                    resposta_buffer += dados.decode()
            except socket.timeout:
                pass

            respostas = resposta_buffer.strip().split("\n")
            for resposta in respostas:
                partes = resposta.strip().split("|")
                if len(partes) != 2:
                    if resposta.strip():
                        print(f"[Cliente] ❌ ACK inválido recebido: {resposta}")
                    continue

                tipo, ack_seq_str = partes
                if not ack_seq_str.isdigit():
                    print(f"[Cliente] ❌ ACK mal formatado: {resposta}")
                    continue

                ack_seq = int(ack_seq_str)

                if 0 <= ack_seq < total_pacotes:
                    if ack_seq in ack_recebido:
                        continue
                    ack_recebido.add(ack_seq)

                    if ack_seq in tempos_envio:
                        rtt = time.time() - tempos_envio[ack_seq]
                        if modo == "GBN":
                            print(f"[Cliente] ⬅️ ACK cumulativo recebido até o pacote {ack_seq} | RTT: {rtt:.3f}s")
                        else:
                            print(f"[Cliente] ⬅️ ACK recebido do pacote {ack_seq} | RTT: {rtt:.3f}s")
                    else:
                        if modo == "GBN":
                            print(f"[Cliente] ⬅️ ACK cumulativo recebido até o pacote {ack_seq}")
                        else:
                            print(f"[Cliente] ⬅️ ACK recebido do pacote {ack_seq}")

                    if modo == "GBN":
                        if ack_seq >= base:
                            base = ack_seq + 1
                    else:  # SR
                        acked[ack_seq] = True
                        while base < total_pacotes and acked[base]:
                            base += 1

        print("\n[Cliente] ✅ Comunicação finalizada.")

if __name__ == "__main__":
    cliente()
