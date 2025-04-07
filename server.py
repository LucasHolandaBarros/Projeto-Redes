from socket import *

HOST = '127.0.0.1'
PORT = 55551

print(f'\nServidor iniciado em {HOST} porta: {PORT}')
print("\nAguardando conexão...")

server = socket(AF_INET, SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5)

con, adr = server.accept()
print(f'Cliente conectado: {adr}\n')

modo = con.recv(1).decode()

if modo == "1":
    print("Modo escolhido: Go-Back-N\n")
elif modo == "2":
    print("Modo escolhido: Repetição Seletiva\n")
else:
    print("Modo inválido! Encerrando o servidor!\n")
    con.close()
    server.close()
    exit()

mensagem_full = ""

while True:
    msg = con.recv(3)
    if not msg:
        print("Conexão encerrada pelo cliente!\n")
        break
    
    msg_decodificada = msg.decode()
    mensagem_full += msg_decodificada
    print(f"Cliente: {msg_decodificada}")

print(f"Mensagem completa recebida: {mensagem_full}\n")
con.send(mensagem_full.encode())

con.close()
server.close()