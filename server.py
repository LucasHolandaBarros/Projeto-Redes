import socket

HOST = '127.0.0.1'
PORT = 5000

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

            # Recebe o modo primeiro
            while "\n" not in buffer:
                buffer += conn.recv(1024).decode()
            modo, buffer = buffer.split("\n", 1)
            modo = modo.strip()
            print(f"[Servidor] Modo de operação: {modo}\n")

            while True:
                data = conn.recv(1024)
                if not data:
                    break
                buffer += data.decode()

                while "\n" in buffer:
                    linha, buffer = buffer.split("\n", 1)
                    partes = linha.strip().split("|")
                    if len(partes) != 3:
                        print("[Servidor] ❌ Pacote inválido:", linha)
                        continue

                    seq_num = int(partes[0])
                    payload = partes[1]
                    checksum = int(partes[2])
                    esperado = calcular_checksum(seq_num, payload)

                    print(f"[Servidor] 📦 Pacote: seq={seq_num}, payload='{payload}', checksum={checksum} (esperado: {esperado})")

                    if checksum == esperado:
                        if seq_num not in pacotes_recebidos:
                            pacotes_recebidos[seq_num] = payload
                            conn.sendall(f"ACK|{seq_num}\n".encode())
                        else:
                            print(f"[Servidor] ✅ Pacote {seq_num} já processado, ACK não enviado novamente.")

            mensagem_final = ''.join(pacotes_recebidos[i] for i in sorted(pacotes_recebidos))
            print(f"\n[Servidor] ✅ Mensagem reconstruída: '{mensagem_final}'")

if __name__ == "__main__":
    servidor()
