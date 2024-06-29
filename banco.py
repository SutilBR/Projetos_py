
class Banco:
    opção = ""
    def __init__(self):
        self.contas={}
        

    def adicionar_contas(self, numero_conta, detalhe_conta):
        if numero_conta in self.contas:
            print(f"A conta {numero_conta} já existe")
        else:
            self.contas[numero_conta] = detalhe_conta
            print(f"A conta {numero_conta} foi adicionada com sucesso. {detalhe_conta}")
        
    def verificar_contas(self, numero_conta):
        if numero_conta in self.contas:
            print(f"Detalhes da conta: {self.contas[numero_conta]}")
        else:
            print(f"A conta {numero_conta} não foi encontrada.")
            bool_conta = input("Você deseja criar uma nova conta? ") 
            if bool_conta == "Sim" or bool_conta == "sim":
                nova_conta = input("Informe o Nº da conta que deseja: ")
                nova_detalhes_nome = input("Digite o nome do titular: ")
                self.adicionar_contas(nova_conta, {"nome_titular": nova_detalhes_nome, "saldo": 0})

    def depositar(self, numero_conta, valor):
        if numero_conta in self.contas:
            self.contas[numero_conta]["saldo"] += valor
            print(f"Seu novo saldo é de R$ {self.contas[numero_conta]['saldo']}")
        else:
            print(f"Por favor, verifique o número da conta, e tente novamente. Conta digitada: {numero_conta}")

    def transferencia(self, numero_conta_recebedora, numero_conta_pagadora, valor):
        pass
    
    def saque(self, numero_conta, valor):
        try: valor = float(valor) # Verificar se o valor é numérico
        except ValueError:
            print("Valor invalido. Por favor, insira um valor numérico.")
            return
        if valor <=0:
            print("O valor do saque debe ser maior que zero.")
            return

        if numero_conta in self.contas:
            if self.contas[numero_conta]["saldo"] > valor:
                self.contas[numero_conta]["saldo"] -= valor
                print(f"você sacou R$ {valor:.2f}. Seu novo saldo é de R$ {self.contas[numero_conta]['saldo']:.2f}")
            else:
                print(f"Não foi possivel continuar com a transação, seu saldo é insuficiente. Seu saldo R$ {self.contas[numero_conta]['saldo']:.2f}.")
        else:
            print("Conta não encontrada, por favor, tente novamente.")

    def historico(self, numero_conta, historico_conta):
        pass

    def menu_principal(self):
        while True:
            menu = ("""
Escolha uma opção abaixo:
[1] Adicionar Conta
[2] Verificar Conta
[3] Realizar Depósito
[4] Realizar Saque
[0] Sair
""")
            opção = input(menu)
            if opção == "1": # Adicionar conta
                nova_conta = input("Informe o Nº da conta que deseja: ")
                nova_detalhes_nome = input("Digite o nome do titular: ")
                self.adicionar_contas(nova_conta, {"nome_titular": nova_detalhes_nome, "saldo": 0})
                
            elif opção == "2": # Verificar conta
                verificar_conta = input("Digite o número da conta que deseja verificar: ")
                self.verificar_contas(verificar_conta)

            elif opção == "3": # Realiza deposito
                deposito_conta = input("Digite o número da conta para o depósito: ")
                try: 
                    deposito_valor = int(input("Digite o valor do depósito: "))
                except ValueError:
                    print("Valor inválido. Por favor, insira um valor númerico")
                    continue # volta ao inicio do loop
                if  deposito_valor <=0:
                    print("O valor do depósito deve ser maior do que zero.")
                    continue # volta ao inicio do loop
                self.depositar(deposito_conta, deposito_valor)

            elif opção == "4": # Realizar saque
                numero_conta_saque = input("Digite o número da conta para o saque: ")
                try: valor_saque = int(input("Digite o valor do saque: "))
                except ValueError: 
                    print("Valor inválido. Por favor, insira um valor númerico")
                    continue # volta ao inicio do loop
                if valor_saque <=0:
                    print("O valor do saque deve ser maior que zero.")
                    continue # volta ao inicio do loop
                self.saque(numero_conta_saque, valor_saque)

            elif opção == "0":
                print("Encerrando o programa...")
                break
                
            else:
                print("Opção inválida. Por favor, escolha uma as opções existentes no MENU")

if __name__ == "__main__":
    Banco = Banco()
    Banco.menu_principal()