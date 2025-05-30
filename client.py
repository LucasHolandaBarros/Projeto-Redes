import socket
import time
import random

HOST = '127.0.0.1'
PORT = 5000
TAMANHO_PACOTE = 3
WINDOW_SIZE = 4
TIMEOUT = 3  # Timeout individual para GBN (em segundos)

def rotl(val, r_bits, max_bits=32):
    return ((val << r_bits) & (2**max_bits - 1)) | (val >> (max_bits - r_bits))

def calcular_hash(seq_num, payload):
    dados = f"{seq_num}|{payload}"
    h = 0xABCDEF
    for i, c in enumerate(dados):
        v = ord(c)
        h ^= (v * (i + 1))
        h = rotl(h, 5)
        h = (h * 31 + 0x5A5A5A5A) & 0xFFFFFFFF
    return f"{h:08X}"

def criar_pacote(seq_num, payload, corromper=False):
    payload = payload.ljust(TAMANHO_PACOTE)
    hash_val = calcular_hash(seq_num, payload)
    if corromper:
        hash_val = hash_val[:-1] + chr((ord(hash_val[-1]) + 1) % 256)
    return f"{seq_num}|{payload}|{hash_val}"

def quebrar_mensagem(msg, limite):
    msg = msg[:limite]
    pacotes = []
    for i in range(0, len(msg), TAMANHO_PACOTE):
        payload = msg[i:i + TAMANHO_PACOTE]
        pacotes.append((i // TAMANHO_PACOTE, payload))
    return pacotes

def enviar_pacote(seq, pacotes, modo_erro, erro_seq, tempos_envio, s, simular_erro, pacote_com_erro):
    agora = time.time()
    seq_num, payload = pacotes[seq]
    pacote = criar_pacote(seq_num, payload)

    if modo_erro == "2" and seq == erro_seq and seq not in tempos_envio:
        print(f"[Cliente] ⏳ Simulando timeout no pacote {seq} (não enviado)")
        tempos_envio[seq] = agora - (TIMEOUT + 1)
        return "timeout"

    elif modo_erro == "3" and seq == erro_seq and seq not in tempos_envio:
        pacote = criar_pacote(seq_num, payload, corromper=True)
        print(f"[Cliente] ⚠️ Simulando erro de hash no pacote {seq}")

    tempos_envio[seq] = agora
    s.sendall((pacote + "\n").encode())
    print(f"[Cliente] ➡️ Enviado pacote {seq}: {pacote}")
    return "enviado"

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

    modo_erro = input("\nEscolha o modo de transmissão\n1 - Sem erros\n2 - Erro no Timeout\n3 - Erro no Hash\n4 - Erro de Ordem\nOpção: ").strip()
    simular_erro = (modo_erro == "2" or modo_erro == "3" or modo_erro == "4")
    pacote_com_erro = -1
    if simular_erro:
        pacotes_validos = [seq for seq, payload in pacotes if payload.strip()]
        if pacotes_validos:
            pacote_com_erro = random.choice(pacotes_validos)
            print(f"\n[Cliente] Pacotes com erro simulado: [{pacote_com_erro}]")
    else:
        print("\n[Cliente] Comunicação SEM erros será utilizada.")

    total_pacotes = len(pacotes)
    fora_de_ordem_enviado = False

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

        while base < total_pacotes:
            while next_seq < base + WINDOW_SIZE and next_seq < total_pacotes:
                if not acked[next_seq]:
                    if modo_erro == "4" and next_seq == pacote_com_erro and not fora_de_ordem_enviado:
                        print(f"[Cliente] ⏩ Pulando temporariamente o pacote {next_seq} para simular fora de ordem")
                        next_seq += 1
                        continue

                    status = enviar_pacote(
                        next_seq, pacotes, modo_erro, pacote_com_erro,
                        tempos_envio, s, simular_erro, pacote_com_erro
                    )
                    if status != "adiar":
                        next_seq += 1

            if modo_erro == "4" and not fora_de_ordem_enviado:
                if pacote_com_erro not in tempos_envio:
                    print(f"[Cliente] 🚀 Enviando agora o pacote fora de ordem: {pacote_com_erro}")
                    seq_num, payload = pacotes[pacote_com_erro]
                    pacote = criar_pacote(seq_num, payload)
                    tempos_envio[pacote_com_erro] = time.time()
                    s.sendall((pacote + "\n").encode())
                    print(f"[Cliente] ➡️ Enviado pacote {pacote_com_erro}: {pacote}")
                    fora_de_ordem_enviado = True

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
                        print(f"[Cliente] ❌ Resposta inválida recebida: {resposta}")
                    continue

                tipo, ack_seq_str = partes
                if not ack_seq_str.isdigit():
                    print(f"[Cliente] ❌ ACK/NACK mal formatado: {resposta}")
                    continue

                ack_seq = int(ack_seq_str)

                if tipo == "NACK":
                    print(f"[Cliente] 🔁 NACK recebido para pacote {ack_seq}. Reenviando imediatamente...")
                    pacote = criar_pacote(*pacotes[ack_seq])
                    tempos_envio[ack_seq] = time.time()
                    s.sendall((pacote + "\n").encode())
                    continue

                if 0 <= ack_seq < total_pacotes:
                    if ack_seq in ack_recebido:
                        continue

                    ack_recebido.add(ack_seq)
                    acked[ack_seq] = True

                    if ack_seq in tempos_envio:
                        rtt = time.time() - tempos_envio[ack_seq]
                        if modo == "GBN":
                            print(f"[Cliente] ⬅️ ACK cumulativo recebido até o pacote {ack_seq} | RTT: {rtt:.3f}s")
                        else:
                            print(f"[Cliente] ⬅️ ACK recebido do pacote {ack_seq} | RTT: {rtt:.3f}s")

                    if modo == "GBN":
                        for i in range(base, ack_seq + 1):
                            acked[i] = True
                            ack_recebido.add(i)
                        base = ack_seq + 1
                        next_seq = base
                    else:
                        while base < total_pacotes and acked[base]:
                            base += 1

            if modo == "GBN" and base < total_pacotes:
                tempo_base = tempos_envio.get(base)
                if tempo_base and (time.time() - tempo_base > TIMEOUT):
                    print("\n[Cliente] ⏳ Timeout atingido. Reenviando pacotes não confirmados...\n")
                    print(f"[Cliente] 🔁 (GBN) Reenviando a partir do pacote {base}")
                    next_seq = base

            if modo == "SR":
                for seq in range(base, min(base + WINDOW_SIZE, total_pacotes)):
                    if not acked[seq]:
                        tempo_envio = tempos_envio.get(seq)
                        if tempo_envio and (time.time() - tempo_envio > TIMEOUT):
                            print(f"\n[Cliente] ⏳ Timeout do pacote {seq}. Reenviando...\n")
                            pacote = criar_pacote(*pacotes[seq])
                            tempos_envio[seq] = time.time()
                            s.sendall((pacote + "\n").encode())
                            print(f"[Cliente] 🔁 Reenvio do pacote {seq}: {pacote}")

        s.sendall(b"FIM\n")
        time.sleep(0.5)
        print("\n[Cliente] ✅ Comunicação finalizada.")

if __name__ == "__main__":
    cliente()
