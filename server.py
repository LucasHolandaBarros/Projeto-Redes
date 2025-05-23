import socket

HOST = '127.0.0.1'
PORT = 5000
WINDOW_SIZE = 4

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
    return h  # retorna inteiro

def servidor():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[Servidor] Aguardando conexão em {HOST}:{PORT}...\n")

        while True:  # Loop para aceitar múltiplas conexões
            conn, addr = s.accept()
            with conn:
                print(f"[Servidor] Conectado por {addr}")

                buffer = ""
                modo = ""
                pacotes_recebidos = {}
                esperado_gbn = 0
                contador_janela = 0
                esperado_sr = 0

                while "\n" not in buffer:
                    dados = conn.recv(1024)
                    if not dados:
                        print("[Servidor] ❌ Conexão encerrada antes de receber o modo.")
                        break
                    buffer += dados.decode()

                if not buffer:
                    continue

                modo, buffer = buffer.split("\n", 1)
                modo = modo.strip()
                print(f"[Servidor] Modo de operação: {modo}\n")

                while True:
                    try:
                        data = conn.recv(1024)
                        if not data:
                            print("[Servidor] 🔌 Conexão encerrada pelo cliente.")
                            break
                        buffer += data.decode()
                        if "FIM\n" in buffer:
                            print("[Servidor] 🚪 Recebido sinal de término do cliente.")
                            break
                    except ConnectionResetError:
                        print("[Servidor] ⚠️ Conexão foi encerrada abruptamente pelo cliente.")
                        break

                    while "\n" in buffer:
                        linha, buffer = buffer.split("\n", 1)
                        linha = linha.strip()
                        if not linha or linha == "FIM":
                            continue

                        if linha.count("|") < 2:
                            buffer = linha + "\n" + buffer
                            break

                        print(f"[Servidor] 🔍 Linha recebida bruta: '{linha}'")

                        partes = linha.split("|")
                        if len(partes) != 3:
                            print("[Servidor] ❌ Pacote inválido:", linha)
                            continue

                        try:
                            seq_num = int(partes[0])
                            payload = partes[1]
                            checksum = int(partes[2], 16)  # Conversão correta do hash em hex
                        except ValueError:
                            print("[Servidor] ❌ Erro ao interpretar pacote:", linha)
                            continue

                        esperado_checksum = calcular_hash(seq_num, payload)
                        print(f"[Servidor] 📦 Pacote: seq={seq_num}, payload='{payload}', checksum={checksum} (esperado: {esperado_checksum})")

                        if modo == "GBN":
                            if checksum == esperado_checksum and seq_num == esperado_gbn:
                                pacotes_recebidos[seq_num] = payload
                                esperado_gbn += 1
                                contador_janela += 1

                                if contador_janela == WINDOW_SIZE:
                                    conn.sendall(f"ACK|{esperado_gbn - 1}\n".encode())
                                    print(f"[Servidor] ✅ ACK cumulativo enviado até o pacote {seq_num}\n")
                                    contador_janela = 0
                            else:
                                ack_para = esperado_gbn - 1
                                if ack_para >= 0:
                                    conn.sendall(f"ACK|{ack_para}\n".encode())
                                    print(f"[Servidor] ❌ Pacote fora de ordem ou corrompido. Reenviando ACK|{ack_para}\n")
                                else:
                                    print("[Servidor] ⚠️ Ignorando pacote inválido antes do início válido.")
                                contador_janela = 0

                        else:  # SR
                            if checksum == esperado_checksum:
                                if seq_num not in pacotes_recebidos:
                                    pacotes_recebidos[seq_num] = payload
                                    print(f"[Servidor] Pacote {seq_num} armazenado.")

                                while esperado_sr in pacotes_recebidos:
                                    conn.sendall(f"ACK|{esperado_sr}\n".encode())
                                    print(f"[Servidor] ✅ ACK ordenado enviado para o pacote {esperado_sr}\n")
                                    esperado_sr += 1
                            else:
                                conn.sendall(f"NACK|{seq_num}\n".encode())
                                print(f"[Servidor] ❌ Checksum inválido para pacote {seq_num}. Enviando NACK|{seq_num}\n")

                if pacotes_recebidos:
                    mensagem_final = ''.join(
                        pacotes_recebidos[i] for i in sorted(pacotes_recebidos)
                        if pacotes_recebidos[i].strip()
                    )
                    print(f"[Servidor] ✅ Mensagem reconstruída: '{mensagem_final}'")
                else:
                    print("[Servidor] ⚠️ Nenhum pacote válido recebido.")

if __name__ == "__main__":
    servidor()
