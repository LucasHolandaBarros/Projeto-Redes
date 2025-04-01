from socket import *

HOST = '127.0.0.1'
PORT = 55551

client = socket(AF_INET, SOCK_STREAM)
client.connect((HOST, PORT))

print("Conexão efetuada com o servidor!")
print(f"\nConexão: Host {HOST} Porta {PORT}\n")

while True:
    msg = input("Digite: ")
    if not msg:
        break
    client.send(msg.encode())

print("\nConexão encerrada com o servidor\n")

client.close()