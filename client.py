import socket
import time
import random

HOST = '127.0.0.1'
PORT = 5000
TAMANHO_PACOTE = 3
WINDOW_SIZE = 4

def calcular_checksum(seq_num, payload):
    soma = seq_num + sum(ord(c) for c in payload)
    return soma % 256

def criar_pacote(seq_num, payload, corromper=False):
    payload = payload.ljust(TAMANHO_PACOTE)
    checksum = calcular_checksum(seq_num, payload)
    if corromper:
        checksum = (checksum + 1) % 256  # Simula corrupção
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

    if modo == "GBN":
        resto = len(pacotes) % WINDOW_SIZE
        if resto != 0:
            pacotes_faltando = WINDOW_SIZE - resto
            inicio_seq = len(pacotes)
            for i in range(pacotes_faltando):
                pacotes.append((inicio_seq + i, ""))

    total_pacotes = len(pacotes)
    pacotes_validos = [seq for seq, payload in pacotes if payload.strip()]
    pacote_com_erro = random.choice(pacotes_validos)
    print(f"[Cliente] Pacotes com erro simulado: [{pacote_com_erro}]")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.settimeout(5)
        s.sendall((modo + "\n").encode())

        print(f"\n[Cliente] Modo: {modo} | Janela: {WINDOW_SIZE} | Total de pacotes: {total_pacotes}\n")

        base = 0
        next_seq = 0
        acked = [False] * total_pacotes
        tempos_envio = {}
        ack_recebido = set()
        timeout_total = 5
        tempo_inicio = time.time()

        while base < total_pacotes:
            # Enviar pacotes dentro da janela
            while next_seq < base + WINDOW_SIZE and next_seq < total_pacotes:
                if not acked[next_seq]:
                    corromper = (next_seq == pacote_com_erro and next_seq not in tempos_envio)
                    pacote = criar_pacote(*pacotes[next_seq], corromper=corromper)
                    tempos_envio[next_seq] = time.time()
                    s.sendall((pacote + "\n").encode())
                    print(f"[Cliente] ➡️ Enviado pacote {next_seq}: {pacote}")
                    if corromper:
                        print(f"[Cliente] ⚠️ Simulando erro no pacote {next_seq}")
                next_seq += 1

            # Esperar por ACKs
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
            ack_recebido_neste_ciclo = False
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
                    acked[ack_seq] = True  # ✅ Marca como ACK antes de usar

                    if ack_seq in tempos_envio:
                        rtt = time.time() - tempos_envio[ack_seq]
                        if modo == "GBN":
                            print(f"[Cliente] ⬅️ ACK cumulativo recebido até o pacote {ack_seq} | RTT: {rtt:.3f}s")
                        else:
                            print(f"[Cliente] ⬅️ ACK recebido do pacote {ack_seq} | RTT: {rtt:.3f}s")

                    if modo == "GBN":
                        if ack_seq >= base:
                            base = ack_seq + 1
                    else:  # SR
                        while base < total_pacotes and acked[base]:
                            base += 1

                    ack_recebido_neste_ciclo = True

            if ack_recebido_neste_ciclo:
                tempo_inicio = time.time()

            if time.time() - tempo_inicio > timeout_total:
                print("\n[Cliente] ⏳ Timeout atingido. Reenviando pacotes não confirmados...\n")
                tempo_inicio = time.time()
                # Não mexa em next_seq! Use variável temporária
                for seq in range(base, min(base + WINDOW_SIZE, total_pacotes)):
                    if not acked[seq]:
                        corromper = False
                        pacote = criar_pacote(*pacotes[seq], corromper=corromper)
                        tempos_envio[seq] = time.time()
                        s.sendall((pacote + "\n").encode())
                        print(f"[Cliente] 🔁 Reenvio do pacote {seq}: {pacote}")

        s.sendall(b"FIM\n")
        print("\n[Cliente] ✅ Comunicação finalizada.")

if __name__ == "__main__":
    cliente()
