import datetime
import sqlite3

class Banco:
    def __init__(self, conexao):
        self.contas={} 
        self.conexao = conexao
        self.cursor = conexao.cursor()
        cursor = conexao.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS historico
                       (id INTEGER PRIMARY KEY, Numero_conta TEXT, Descricao TEXT, Saldo REAL, Status TEXT, Data TEXT)""")
        conexao.commit()
        cursor.execute("""CREATE TABLE IF NOT EXISTS user
                       (id INTEGER PRIMARY KEY, Numero_conta TEXT, nome TEXT, senha text, Data TEXT)""")
        conexao.commit()

    def adicionar_conta(self, numero_conta, detalhe_conta, senha, data):
        """
        Adicionar contas, fazendo a verificação se essa conta já existe
        
        Args:
            numero_conta: numero da conta
            detalhe_conta: detalhe da conta, nome, e saldo
            data: Data e hora, usado para sabermos no historico a data de movimentação
        """
        self.cursor.execute("SELECT * FROM user WHERE Numero_conta = ?", (numero_conta,))
        resultado = self.cursor.fetchone()
        if resultado: # se a conta já existir irá aparecer essa mensagem
            print(f"A conta {numero_conta} Já existe")
            return False
        else: # Cria a conta e adiciona o histórico dela
            self.contas[numero_conta] = {"detalhe_conta": detalhe_conta, "historico":[]}
            self.historico(numero_conta, "Conta criada", 0, True, data)
            self.historico_cadastro(numero_conta, detalhe_conta["nome_titular"], senha, data)
            print(f"A conta {numero_conta} foi adicionada com sucesso. {detalhe_conta}")
        
    def verificar_conta(self, numero_conta, data):
        """
        Verificar a conta, se a conta não existe, iremos verificar se a pessoa quer fazer uma conta

        Args:
            numero_conta: numero da conta
            data: data
        """

        self.cursor.execute("SELECT * FROM user WHERE Numero_conta = ?", (numero_conta,))
        resultado = self.cursor.fetchone()
        if resultado:
            detalhes_conta = self.contas[numero_conta]["detalhe_conta"]
            saldo = detalhes_conta["saldo"]
            print(f"Detalhes da conta: {detalhes_conta}")
            self.historico(numero_conta, "Conta verificada", saldo, True, data)
            conta_historico = self.contas[numero_conta]["historico"]
            print(f"Histórico da conta: \n {conta_historico}")
        else: # a conta não existe, e dá a opção de criar uma nova conta
            print(f"A conta {numero_conta} não foi encontrada.")
            bool_conta = input("Você deseja criar uma nova conta? (Sim/Não)") 
            if bool_conta.lower() == "sim":
                nova_conta = input("Informe o Nº da conta que deseja: ")
                nova_detalhes_nome = input("Digite o nome do titular: ")
                self.adicionar_conta(nova_conta, {"nome_titular": nova_detalhes_nome, "saldo": 0}, data)
            else:
                print("Não entendi a sua resposta. Voltando para o Menu...")

    def depositar(self, numero_conta, valor, data):
        """
        Função para realizar o depósito, é verificado se a conta existe

        Args:
            numero_conta: numero da conta
            valor: valor do depósito
            data: data
        """
        self.cursor.execute("SELECT * FROM user WHERE Numero_conta = ?", (numero_conta,))
        resultado = self.cursor.fetchone()
        if resultado:
            self.contas[numero_conta]["detalhe_conta"]["saldo"] += valor
            novo_saldo = self.contas[numero_conta]["detalhe_conta"]["saldo"]
            print(f"Seu novo saldo é de R$ {novo_saldo}")
            self.historico(numero_conta, "Depósito", novo_saldo, True, data)
        else: # a conta não foi encontrada
            print(f"Conta {numero_conta} não encontrada, por favor, tente novamente.")

    def transferencia(self, numero_conta_pagadora, numero_conta_recebedora, valor, data):
        """
        Função para realizar transferencia entre contas existentes

        Args:
            numero_conta_recebedora: numero da conta que irá receber o dinheiro
            numero_conta_pagadora: numero da conta que irá pagar
            valor: valor da transferencia
            data: data da transação
        """
        self.cursor.execute("SELECT * FROM user WHERE Numero_conta = ?", (numero_conta_pagadora,))
        resultado = self.cursor.fetchone()
        if resultado:
            self.cursor.execute("SELECT * FROM user WHERE Numero_conta = ?", (numero_conta_recebedora,))
            resultado = self.cursor.fetchone()
            if resultado:
                if self.contas[numero_conta_pagadora]["detalhe_conta"]["saldo"] >= valor:
                    self.contas[numero_conta_recebedora]["detalhe_conta"]["saldo"] += valor
                    self.contas[numero_conta_pagadora]["detalhe_conta"]["saldo"] -= valor
                    print(f"Transferência realizada com sucesso. Seu novo saldo é {self.contas[numero_conta_pagadora]['detalhe_conta']['saldo']}")
                    self.historico(numero_conta_pagadora, "Transferencia Débito", self.contas[numero_conta_pagadora]['detalhe_conta']['saldo'], True, data)
                    self.historico(numero_conta_recebedora, "Transferencia Crédito", self.contas[numero_conta_recebedora]['detalhe_conta']['saldo'], True, data)
                else:
                    print(f"Saldo insuficiente. Seu saldo é de R$ {self.contas[numero_conta_pagadora]['detalhe_conta']['saldo']}")
                    self.historico(numero_conta_pagadora, "Transferencia Débito", self.contas[numero_conta_pagadora]['detalhe_conta']['saldo'], False, data)
            else:
                print(f"A conta {numero_conta_recebedora}, não existe.")
        else:
            print(f"A conta {numero_conta_pagadora}, não existe.")

    def saque(self, numero_conta, valor, data):
        """
        Realiza o saque, verifica se na conta existe saldo e faz o saque. mostra o novo valor do saldo após o saque

        Args:
            numero_conta: numero da conta
            valor: valor do saque
            data: data
        """
        try:  
            valor = float(valor) # Verificar se o valor é numérico
        except ValueError: # tratamento de erro para se o valor não for numérico
            print("Valor invalido. Por favor, insira um valor numérico.")
            return
        if valor <=0: # verifica se o saque é maior que zero
            print("O valor do saque deve ser maior que zero.")
            return

        self.cursor.execute("SELECT * FROM user WHERE Numero_conta = ?", (numero_conta,))
        resultado = self.cursor.fetchone()
        if resultado:
            if self.contas[numero_conta]["detalhe_conta"]["saldo"] > valor:
                self.contas[numero_conta]["detalhe_conta"]["saldo"] -= valor
                novo_saldo = self.contas[numero_conta]["detalhe_conta"]["saldo"]
                print(f"você sacou R$ {valor:.2f}. Seu novo saldo é de R$ {novo_saldo:.2f}")
                self.historico(numero_conta, "Saque", novo_saldo, True, data)
            else: # se a conta não possuir o saldo necessário para o saque, irá aparecer mensagem de saldo insuficiente
                print(f"Não foi possivel continuar com a transação, seu saldo é insuficiente. Seu saldo R$ {self.contas[numero_conta]['detalhe_conta']['saldo']:.2f}.")
                self.historico(numero_conta, "Saque", self.contas[numero_conta]['detalhe_conta']['saldo'], False, data)
        else: # a conta não foi encontrada
            print("Conta não encontrada, por favor, tente novamente.")

    def historico(self, numero_conta, tipo, valor, bool_teste, data): # tipo(saque, deposito, criação), valor, status, data e hora
        """
        historico de movimentação na conta, tentativas de saques, depositos, e a criação da conta

        Args:
            numero_conta: numero da conta
            tipo: tipo de movimentação (deposito, saque, criação, verificação)
            valor: valor da conta
            bool_teste: se a movimentação foi realizada (true) ou foi recusada (false)
            data: data
        """
        historico = {
            "Numero_conta": numero_conta,
            "Descricao": tipo,
            "Saldo": float(valor),
            "Status": "Sucesso" if bool_teste else "Falha",
            "Data": data.strftime("%d-%m-%Y %H:%M:%S")
        }
        self.contas[numero_conta]["historico"].append(historico)
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO historico (Numero_conta, Descricao, Saldo, Status, Data) VALUES (?, ?, ?, ?, ?)",
                        (historico["Numero_conta"], historico["Descricao"], historico["Saldo"], historico["Status"], historico["Data"]))
        conexao.commit()

    def historico_cadastro(self, numero_conta, nome, senha, data):
        historico_cadastro = {
            "Numero_conta": numero_conta,
            "Nome": nome,
            "Password": senha,
            "Data": data.strftime("%d-%m-%Y %H:%M:%S")
            }
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO user (Numero_conta, Nome, senha, Data) VALUES (?, ?, ?, ?)",
                    (historico_cadastro["Numero_conta"], historico_cadastro["Nome"], historico_cadastro["Password"], historico_cadastro["Data"]))
        conexao.commit()

    def menu_principal(self):
        """Menu interativo para os usuarios com as opções para o sistema"""
        
        while True:
            menu = ("""
Escolha uma opção abaixo:
[1] Adicionar Conta
[2] Verificar Conta
[3] Realizar Depósito
[4] Realizar Saque
[5] Realizar transferência
[0] Sair
""")
            opção = input(menu)
            data_transação = datetime.datetime.now()

            if opção == "1": # Adicionar conta
                nova_conta = input("Informe o Nº da conta que deseja: ")
                nova_detalhes_nome = input("Digite o nome do titular: ")
                nova_senha = input("Informe a senha da conta: ")
                self.adicionar_conta(nova_conta, {"nome_titular": nova_detalhes_nome, "saldo": 0}, nova_senha, data_transação)
                
            elif opção == "2": # Verificar conta
                verificar_conta = input("Digite o número da conta que deseja verificar: ")
                self.verificar_conta(verificar_conta, data_transação)

            elif opção == "3": # Realiza deposito
                deposito_conta = input("Digite o número da conta para o depósito: ")
                try: 
                    deposito_valor = float(input("Digite o valor do depósito: "))
                except ValueError:
                    print("Valor inválido. Por favor, insira um valor númerico")
                    continue # volta ao inicio do loop
                if  deposito_valor <=0:
                    print("O valor do depósito deve ser maior do que zero.")
                    continue # volta ao inicio do loop
                self.depositar(deposito_conta, deposito_valor, data_transação)

            elif opção == "4": # Realizar saque
                numero_conta_saque = input("Digite o número da conta para o saque: ")
                try: valor_saque = float(input("Digite o valor do saque: "))
                except ValueError: 
                    print("Valor inválido. Por favor, insira um valor númerico")
                    continue # volta ao inicio do loop
                if valor_saque <=0:
                    print("O valor do saque deve ser maior que zero.")
                    continue # volta ao inicio do loop
                self.saque(numero_conta_saque, valor_saque, data_transação)

            elif opção == "5": # Realizar transferencia
                numero_conta_pagadora = input("Digite o número da conta pagadora: ")
                numero_conta_recebedora = input("Digite o número da conta que irá receber: ")
                if numero_conta_pagadora != numero_conta_recebedora:
                    try: valor_transferencia = float(input("Digite o valor da transferência: "))
                    except ValueError:
                        print("O valor digitado é inválido")
                        continue # volta ao inicio do loop
                    if valor_transferencia <=0:
                        print("O valor da transferencia deve ser maior que zero.")
                        continue
                    self.transferencia(numero_conta_pagadora, numero_conta_recebedora, valor_transferencia, data_transação)
                else:
                    print("As contas não podem ser iguais.")

            elif opção == "0":
                print("Encerrando o programa...")
                self.conexao.close()
                break
                
            else:
                print("Opção inválida. Por favor, escolha uma as opções existentes no MENU")

if __name__ == "__main__":
    conexao = sqlite3.connect("Banco.db")
    Banco = Banco(conexao)
    Banco.menu_principal()