from socket import *

HOST = '127.0.0.1'
PORT = 55551

client = socket(AF_INET, SOCK_STREAM)
client.connect((HOST, PORT))

print("Conexão efetuada com o servidor!")
print(f"\nConexão: Host {HOST} Porta {PORT}\n")

print("Digite a quantidade de caracteres a ser digitado: ")
qntd = int(input())

while True:
    msg = input("Digite: ")
    if len(msg) <= qntd:
        client.send(msg.encode("utf-8"))
    else:
        msg = msg[:qntd]
        client.send(msg.encode("utf-8"))
    if not msg:
        break

print("\nConexão encerrada com o servidor\n")

client.close()