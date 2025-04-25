import time
from socket import *

def calcular_checksum(dados):
    return sum(dados.encode()) % 256

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
timeout = 2  # Tempo de espera em segundos para o ACK

while total_enviado < qntd_total:
    restante = qntd_total - total_enviado
    mensagem = input(f"Digite 'fim' p/ sair: ")

    if mensagem.lower() == "fim":
        break

    mensagem = mensagem[:restante]
    i = 0
    while i < len(mensagem):
        payload = mensagem[i:i+3]
        checksum = calcular_checksum(payload)
        pacote = f"{seq_num}|{payload}|{checksum}"
        
        # Marca o início do envio
        start_time = time.time()
        
        client.send(pacote.encode())
        print(f"[CLIENTE] Enviado pacote #{seq_num} com carga '{payload}' e checksum {checksum}")
        
        # Começando o temporizador para esperar pelo ACK
        ack_recebido = False
        while not ack_recebido:
            ack = client.recv(1024).decode()
            if ack:  # Se o ACK for recebido
                ack_recebido = True
                # Marca o fim do tempo de recebimento do ACK
                end_time = time.time()
                tempo_transmissao = end_time - start_time
                print(f"[CLIENTE] ACK {seq_num} confirmado. Tempo de transmissão: {tempo_transmissao:.4f} segundos.")
            elif time.time() - start_time > timeout:  # Se o tempo de espera foi excedido
                print(f"[CLIENTE] Timeout. Reenviando pacote #{seq_num}")
                client.send(pacote.encode())  # Reenvia o pacote
                start_time = time.time()  # Reinicia o temporizador

        seq_num += 1
        total_enviado += len(payload)
        i += 3

print("\nFim do envio. Encerrando conexão.")
client.send(b"fim")
client.close()
