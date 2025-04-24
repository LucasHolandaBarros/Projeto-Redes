from socket import *

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

    if "|" in pacote:
        seq_str, payload = pacote.split("|", 1)
        print(f"[SERVIDOR] Pacote #{seq_str} recebido com carga: '{payload}'")
        mensagem_completa += payload
        total_recebido += len(payload)

        ack = f"ACK {seq_str}"
        con.send(ack.encode())
    else:
        print("[SERVIDOR] Pacote inválido (sem '|')")
        con.send(b"ACK ?")  # resposta para pacote mal formatado

print(f"\n[SERVIDOR] Mensagem reconstruída: {mensagem_completa}")
con.close()
server.close()