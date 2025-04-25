from socket import *
import time

def calcular_checksum(dados):
    return sum(dados.encode()) % 256

HOST = '127.0.0.1'
PORT = 55551

server = socket(AF_INET, SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5)

print(f"\n[Servidor] Aguardando conexão em {HOST}:{PORT}...")
con, addr = server.accept()
print(f"[Servidor] Conectado ao cliente: {addr}")

# Modo de operação
modo = con.recv(1).decode()
if modo == "1":
    print("\nModo escolhido pelo cliente: Go-Back-N")
elif modo == "2":
    print("\nModo escolhido pelo cliente: Repetição Seletiva")
else:
    print("\nModo inválido! Encerrando servidor.")
    con.close()
    server.close()
    exit()

# Quantidade esperada de caracteres
qntd_total = int(con.recv(1024).decode())
print(f"[Servidor] Cliente pretende enviar aproximadamente {qntd_total} caracteres.\n")

mensagem_completa = ""
total_recebido = 0

while True:
    pacote = con.recv(1024).decode()
    if not pacote or pacote.lower() == "fim":
        print("\n[Servidor] Comunicação encerrada pelo cliente.")
        break

    partes = pacote.split("|")
    if len(partes) == 3:
        seq_str, payload, recebido_checksum = partes
        calculado_checksum = calcular_checksum(payload)

        if int(recebido_checksum) == calculado_checksum:
            print(f"[SERVIDOR] Pacote #{seq_str} OK. Payload: '{payload}'")
            mensagem_completa += payload
            total_recebido += len(payload)
            ack = f"ACK {seq_str}"
        else:
            print(f"[SERVIDOR] ERRO de checksum no pacote #{seq_str}")
            ack = f"NAK {seq_str}"
        con.send(ack.encode())
    else:
        print("[SERVIDOR] Pacote mal formatado.")
        con.send(b"ACK ?")

print(f"\n[SERVIDOR] Mensagem reconstruída: {mensagem_completa}")
con.close()
server.close()
