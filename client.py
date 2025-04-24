from socket import *

HOST = '127.0.0.1'
PORT = 55551

client = socket(AF_INET, SOCK_STREAM)
client.connect((HOST, PORT))

# Escolha de modo
print("\nEscolha o modo de operação:")
print("[1] - Go-Back-N")
print("[2] - Repetição Seletiva")
modo = input("Digite o número da operação: ")
client.send(modo.encode())

if modo == "1":
    print("\nModo escolhido: Go-Back-N")
elif modo == "2":
    print("\nModo escolhido: Repetição Seletiva")
else:
    print("\nModo inválido! Encerrando conexão.")
    client.close()
    exit()

# Limite de caracteres
print("\nDigite o total estimado de caracteres a enviar:")
qntd_total = int(input("Total: "))
client.send(str(qntd_total).encode())

seq_num = 0
total_enviado = 0

while total_enviado < qntd_total:
    restante = qntd_total - total_enviado
    mensagem = input(f"Digite 'fim' p/ sair: ")

    if mensagem.lower() == "fim":
        break

    mensagem = mensagem[:restante]  # Garante que não ultrapassa o limite
    i = 0
    while i < len(mensagem):
        payload = mensagem[i:i+3]
        pacote = f"{seq_num}|{payload}"
        client.send(pacote.encode())
        print(f"[CLIENTE] Enviado pacote #{seq_num} com carga '{payload}'")

        ack = client.recv(1024).decode()
        print(f"[CLIENTE] Recebido: {ack}")

        seq_num += 1
        total_enviado += len(payload)
        i += 3

print("\nFim do envio. Encerrando conexão.")
client.send(b"fim")
client.close()