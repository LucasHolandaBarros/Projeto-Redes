from socket import *

HOST = '127.0.0.1'
PORT = 55551

print("\nEscolha o modo de operação: ")
print("[1] - Go-Back-N")
print("[2] - Repetição Seletiva")
modo = input("Digite o número da operação: ")

print("Enviando SYN")
client = socket(AF_INET, SOCK_STREAM)
client.connect((HOST, PORT))

print("\nACK recebido do servidor")
print("\nConexão efetuada com o servidor!")
print(f"Conexão: Host {HOST} Porta {PORT}\n")

client.send(modo.encode())

if modo == "1":
    print("\nModo escolhido: Go-Back-N")
elif modo == "2":
    print("\nModo escolhido: Repetição Seletiva")
else:
    print("\nModo invalido!")
    print("Encerrando a conexao com o servidor...")
    exit()

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