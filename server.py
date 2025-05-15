import socket

HOST = '127.0.0.1'
PORT = 5000
WINDOW_SIZE = 4

def calcular_checksum(seq_num, payload):
    soma = seq_num + sum(ord(c) for c in payload)
    return soma % 256

def servidor():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[Servidor] Aguardando conexão em {HOST}:{PORT}...\n")

        conn, addr = s.accept()
        with conn:
            print(f"[Servidor] Conectado por {addr}")

            buffer = ""
            modo = ""
            pacotes_recebidos = {}
            esperado_gbn = 0
            contador_janela = 0

            while "\n" not in buffer:
                dados = conn.recv(1024)
                if not dados:
                    print("[Servidor] ❌ Conexão encerrada antes de receber o modo.")
                    return
                buffer += dados.decode()

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
                        buffer = buffer.replace("FIM\n", "")
                        print("[Servidor] 🚪 Recebido sinal de término do cliente.")
                        break
                except ConnectionResetError:
                    print("[Servidor] ⚠️ Conexão foi encerrada abruptamente pelo cliente.")
                    break

                while "\n" in buffer:
                    linha, buffer = buffer.split("\n", 1)
                    if not linha.strip():
                        continue

                    print(f"[Servidor] 🔍 Linha recebida bruta: '{linha}'")

                    partes = linha.strip().split("|")
                    if len(partes) != 3:
                        print("[Servidor] ❌ Pacote inválido:", linha)
                        continue

                    try:
                        seq_num = int(partes[0])
                        payload = partes[1]
                        checksum = int(partes[2])
                    except ValueError:
                        print("[Servidor] ❌ Erro ao interpretar pacote:", linha)
                        continue

                    esperado_checksum = calcular_checksum(seq_num, payload)
                    print(f"[Servidor] 📦 Pacote: seq={seq_num}, payload='{payload}', checksum={checksum} (esperado: {esperado_checksum})")

                    if modo == "GBN":
                        if checksum == esperado_checksum and seq_num == esperado_gbn:
                            pacotes_recebidos[seq_num] = payload
                            esperado_gbn += 1
                            contador_janela += 1

                            if contador_janela == WINDOW_SIZE:
                                conn.sendall(f"ACK|{seq_num}\n".encode())
                                print(f"[Servidor] ✅ ACK cumulativo enviado até o pacote {seq_num}\n")
                                contador_janela = 0
                        else:
                            ack_para = esperado_gbn - 1
                            if ack_para >= 0:
                                conn.sendall(f"ACK|{ack_para}\n".encode())
                                print(f"[Servidor] ❌ Pacote fora de ordem ou corrompido. Reenviando ACK|{ack_para}\n")
                            else:
                                print("[Servidor] ⚠️ Ignorando pacote inválido antes do início válido.")
                            contador_janela = 0  # reinicia a janela

                    else:  # SR
                        if checksum == esperado_checksum:
                            if seq_num not in pacotes_recebidos:
                                pacotes_recebidos[seq_num] = payload
                            conn.sendall(f"ACK|{seq_num}\n".encode())
                            print(f"[Servidor] ✅ ACK individual enviado para o pacote {seq_num}\n")
                        else:
                            print(f"[Servidor] ❌ Checksum inválido para pacote {seq_num}. Ignorado.\n")

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
