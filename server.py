from socket import *

HOST = '127.0.0.1'
PORT = 55551

print(f'Servidor iniciado em {HOST} porta: {PORT}')
print("\nAguardando conexão...")

server = socket(AF_INET, SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5)

con, adr = server.accept()
print(f'Cliente conectado: {adr}')

mensagem_full = ""

while True:
    msg = con.recv(3)
    if not msg:
        print("\nConexão encerrada pelo cliente!\n")
        break
    
    msg_decodificada = msg.decode()
    mensagem_full += msg_decodificada
    print(f"Cliente: {msg_decodificada}")

print(f"Mensagem completa recebida: {mensagem_full}\n")
con.send(mensagem_full.encode())

con.close()
server.close()