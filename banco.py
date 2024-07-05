import datetime
import sqlite3
import hashlib
import secrets

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
                       (id INTEGER PRIMARY KEY, Numero_conta TEXT, nome TEXT, senha TEXT, salt TEXT, Data TEXT)""")
        conexao.commit()

    @staticmethod
    def hash_senha(senha):
        salt = secrets.token_hex(16) # Gerar um salt seguro usando secrets, 16 bytes de salt em formato hex
        hasher = hashlib.sha256() # Criar um objeto de hash SHA-256
        senha_com_salt = senha.encode('utf-8') + salt.encode('utf-8') # Concatenar a senha com o salt
        #Calcular o hash da senha com salt
        hasher.update(senha_com_salt)
        hash_resultante = hasher.hexdigest()
        return hash_resultante, salt # Retornar o hash_resultante e o salt para armazenamento no banco de dados

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
        if resultado: # Se a conta já existir irá aparecer essa mensagem
            print(f"A conta {numero_conta} Já existe")
            return False
        else: # Cria a conta e adiciona o histórico dela
            # Gerar o hash dasenha e o salt
            hash_senha, salt = self.hash_senha(senha)
            # Historico
            self.historico(numero_conta, "Conta criada", 0, True, data)
            self.historico_cadastro(numero_conta, detalhe_conta["nome_titular"], hash_senha, salt, data)
            print(f"A conta {numero_conta} foi adicionada com sucesso. {detalhe_conta}")
    
    def verificar_senha(self, numero_conta, senha):
        """Verifica se a senha fornecida corresponde a senha armazenada
        Args:
        numero_conta: numero da conta
        senha: senha fornecida pelo usuario

        returns:
        true se a senha está correta, false se não estiver correta
        """
        self.cursor.execute("SELECT senha, salt FROM user WHERE Numero_conta = ?", (numero_conta,))
        resultado = self.cursor.fetchone()

        if resultado:
            hash_armazenado = resultado[0]
            salt = resultado[1]
            #calcular ohash da senha fornecida pelo usuário com o salt armazenado
            hasher = hashlib.sha256()
            senha_com_salt = senha.encode('utf-8') + salt.encode('utf-8')
            hasher.update(senha_com_salt)
            hash_fornecido = hasher.hexdigest()

            # comparar os hasher
            if hash_fornecido == hash_armazenado:
                return True
            else:
                return False
        else:
            return False
        
    def verificar_conta(self, numero_conta, senha, data):
        """
        Verificar a conta, se a conta não existe, iremos verificar se a pessoa quer fazer uma conta

        Args:
            numero_conta: numero da conta
            data: data
        """

        self.cursor.execute("SELECT * FROM user WHERE Numero_conta = ?", (numero_conta,))
        resultado = self.cursor.fetchone()
        if resultado:
            resultado = self.verificar_senha(numero_conta, senha)
            if resultado:
                detalhes_conta = """
                SELECT *
                FROM historico
                WHERE Numero_conta = ?
                """
                self.cursor.execute(detalhes_conta, (numero_conta,))
                detalhes_conta = self.cursor.fetchall()
                print(f"Detalhes da conta {numero_conta} \n {detalhes_conta}\n")
                saldo = """
                SELECT Saldo 
                FROM historico 
                WHERE Numero_conta = ? 
                ORDER BY id DESC 
                LIMIT 1"""
                self.cursor.execute(saldo,(numero_conta,))
                resultado = self.cursor.fetchone()
                saldo = resultado[0]
                print(f"Seu saldo é de R$ {saldo}")
                self.historico(numero_conta, "Conta verificada", saldo, True, data)
            else:
                print("Senha fornecida incorreta. Por favor, tente novamente")
        else: # a conta não existe, e dá a opção de criar uma nova conta
            print(f"A conta {numero_conta} não foi encontrada.")
            bool_conta = input("Você deseja criar uma nova conta? (Sim/Não)") 
            if bool_conta.lower() == "sim":
                nova_conta = input("Informe o Nº da conta que deseja: ")
                nova_detalhes_nome = input("Digite o nome do titular: ")
                self.adicionar_conta(nova_conta, {"nome_titular": nova_detalhes_nome, "saldo": 0}, data)
            elif bool_conta.lower() == "não":
                print("Retornando para o Menu")
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

    def transferencia(self, numero_conta_pagadora, numero_conta_recebedora, valor, senha, data):
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
                resultado = self.verificar_senha(numero_conta_pagadora, senha)
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
                    print("Senha incorreta. Por favor, tente novamente.")
            else:
                print(f"A conta {numero_conta_recebedora}, não existe.")
        else:
            print(f"A conta {numero_conta_pagadora}, não existe.")

    def saque(self, numero_conta, valor, senha, data):
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
            resultado = self.verificar_senha(numero_conta, senha)
            if resultado:
                if self.contas[numero_conta]["detalhe_conta"]["saldo"] > valor:
                    self.contas[numero_conta]["detalhe_conta"]["saldo"] -= valor
                    novo_saldo = self.contas[numero_conta]["detalhe_conta"]["saldo"]
                    print(f"você sacou R$ {valor:.2f}. Seu novo saldo é de R$ {novo_saldo:.2f}")
                    self.historico(numero_conta, "Saque", novo_saldo, True, data)
                else: # se a conta não possuir o saldo necessário para o saque, irá aparecer mensagem de saldo insuficiente
                    print(f"Não foi possivel continuar com a transação, seu saldo é insuficiente. Seu saldo R$ {self.contas[numero_conta]['detalhe_conta']['saldo']:.2f}.")
                    self.historico(numero_conta, "Saque", self.contas[numero_conta]['detalhe_conta']['saldo'], False, data)
            else:
                print("Senha fornecida incorreta. Por favor, tente novamente.")
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
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO historico (Numero_conta, Descricao, Saldo, Status, Data) VALUES (?, ?, ?, ?, ?)",
                        (historico["Numero_conta"], historico["Descricao"], historico["Saldo"], historico["Status"], historico["Data"]))
        conexao.commit()

    def historico_cadastro(self, numero_conta, nome, senha, salt, data):
        historico_cadastro = {
            "Numero_conta": numero_conta,
            "Nome": nome,
            "Password": senha,
            "Salt": salt,
            "Data": data.strftime("%d-%m-%Y %H:%M:%S")
            }
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO user (Numero_conta, Nome, senha, Salt, Data) VALUES (?, ?, ?, ?, ?)",
                    (historico_cadastro["Numero_conta"], historico_cadastro["Nome"], historico_cadastro["Password"], historico_cadastro["Salt"], historico_cadastro["Data"]))
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
                verificar_senha = input(f"Digite a sua senha da conta {verificar_conta}: ")
                self.verificar_conta(verificar_conta, verificar_senha, data_transação)

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
                saque_numero_conta = input("Digite o número da conta para o saque: ")
                saque_senha = input(f"Digite a sua senha da conta {saque_numero_conta}: ")
                try: saque_valor = float(input("Digite o valor do saque: "))
                except ValueError: 
                    print("Valor inválido. Por favor, insira um valor númerico")
                    continue # volta ao inicio do loop
                if saque_valor <=0:
                    print("O valor do saque deve ser maior que zero.")
                    continue # volta ao inicio do loop
                self.saque(saque_numero_conta, saque_valor, saque_senha, data_transação)

            elif opção == "5": # Realizar transferencia
                numero_conta_pagadora = input("Digite o número da conta pagadora: ")
                senha_conta_pagadora = input(f"digite a senha da conta {numero_conta_pagadora}: ")
                numero_conta_recebedora = input("Digite o número da conta que irá receber: ")
                if numero_conta_pagadora != numero_conta_recebedora:
                    try: valor_transferencia = float(input("Digite o valor da transferência: "))
                    except ValueError:
                        print("O valor digitado é inválido")
                        continue # volta ao inicio do loop
                    if valor_transferencia <=0:
                        print("O valor da transferencia deve ser maior que zero.")
                        continue
                    self.transferencia(numero_conta_pagadora, numero_conta_recebedora, valor_transferencia, senha_conta_pagadora, data_transação)
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