import datetime
import sqlite3
import hashlib
import secrets
import tkinter as tk
import sys
conta = ""
nome = ""
senha = ""
valor_banco = ""

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
            janela_adicionar = tk.Toplevel()
            janela_adicionar.title("A conta já existe")
            janela_adicionar.geometry("300x50")
            label_conta = tk.Label(janela_adicionar, text=f"Desculpe, a conta  informada já existe no nosso sistema.")
            label_conta.pack(pady=10)
            janela_adicionar.mainloop()
            return False
        else: # Cria a conta e adiciona o histórico dela
            # Gerar o hash dasenha e o salt
            hash_senha, salt = self.hash_senha(senha)
            # Historico
            self.historico(numero_conta, "Conta criada", 0, True, data)
            self.historico_cadastro(numero_conta, detalhe_conta["nome_titular"], hash_senha, salt, data)
            janela_adicionar = tk.Toplevel()
            janela_adicionar.title("Conta Adicionada com sucesso")
            label_conta = tk.Label(janela_adicionar, text=f"A conta {numero_conta} foi adicionada com sucesso")
            label_conta.pack(pady=10)
            janela_adicionar.mainloop()
    
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
                for detalhes in detalhes_conta:
                    print(detalhes)
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
            print(f"A conta {numero_conta} não foi encontrada.\nSe você deseja criar uma nova conta, por favor clique em 'Adicionar Conta' no menu principal.")

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
            detalhe_contas = """
            SELECT Saldo
            FROM historico
            WHERE Numero_conta = ?
            ORDER BY id DESC
            LIMIT 1"""
            self.cursor.execute(detalhe_contas, (numero_conta,))
            resultado = self.cursor.fetchone()
            saldo = resultado[0]
            saldo += valor
            print(f"Seu novo saldo é de R$ {saldo:.2f}")
            self.historico(numero_conta, "Depósito", saldo, True, data)
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
                    detalhe_contas = """
                    SELECT Saldo
                    FROM historico
                    WHERE Numero_conta = ?
                    ORDER BY id DESC
                    LIMIT 1"""
                    self.cursor.execute(detalhe_contas, (numero_conta_pagadora,))
                    resultado = self.cursor.fetchone()
                    saldo_pagadora = resultado[0]
                    if saldo_pagadora >= valor:
                        detalhe_contas = """
                        SELECT Saldo
                        FROM historico
                        WHERE Numero_conta = ?
                        ORDER BY id DESC
                        LIMIT 1"""
                        self.cursor.execute(detalhe_contas, (numero_conta_recebedora,))
                        resultado = self.cursor.fetchone()
                        saldo_recebedora = resultado[0]
                        saldo_recebedora += valor
                        saldo_pagadora -= valor
                        print(f"Transferência realizada com sucesso. Seu novo saldo é {saldo_pagadora}")
                        self.historico(numero_conta_pagadora, "Transferencia Débito", saldo_pagadora, True, data)
                        self.historico(numero_conta_recebedora, "Transferencia Crédito", saldo_recebedora, True, data)
                    else:
                        print(f"Saldo insuficiente. Seu saldo é de R$ {saldo_pagadora}")
                        self.historico(numero_conta_pagadora, "Transferencia Débito", saldo_pagadora, False, data)
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
                detalhe_contas = """
                SELECT Saldo
                FROM historico
                WHERE Numero_conta = ?
                ORDER BY id DESC
                LIMIT 1"""
                self.cursor.execute(detalhe_contas, (numero_conta,))
                resultado = self.cursor.fetchone()
                saldo = resultado[0]
                if saldo >= valor:
                    saldo -= valor
                    print(f"você sacou R$ {valor:.2f}. Seu novo saldo é de R$ {saldo:.2f}")
                    self.historico(numero_conta, "Saque", saldo, True, data)
                else: # se a conta não possuir o saldo necessário para o saque, irá aparecer mensagem de saldo insuficiente
                    print(f"Não foi possivel continuar com a transação, seu saldo é insuficiente. Seu saldo R$ {saldo:.2f}.")
                    self.historico(numero_conta, "Saque", saldo, False, data)
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
        
        menu = ("""
Escolha uma opção abaixo:
[1] Adicionar Conta
[2] Verificar Conta
[3] Realizar Depósito
[4] Realizar Saque
[5] Realizar transferência
[0] Sair
""")
            
        botoes = ["button_verificar", "button_adicionar", "button_deposito", "button_saque", "button_transferencia"]

        def on_adicionar(): # Adicionar conta
            data_transação = datetime.datetime.now()
            def pegar_valor():
                conta = entry_conta.get()
                nome = entry_nome.get()
                senha = entry_senha.get()
                janela_adicionar.destroy()
                if conta and nome and senha:
                    Banco.adicionar_conta(conta, {"nome_titular": nome, "saldo": 0}, senha, data_transação)
                else:
                    print("Por favor, preencha todos os campos.")
            janela_adicionar = tk.Toplevel()
            janela_adicionar.title("Adicionar Conta")

            # Label e Entry para inserir o número da conta
            label_conta = tk.Label(janela_adicionar, text="Insira o número da Conta que você deseja:")
            label_conta.pack(pady=10)

            entry_conta = tk.Entry(janela_adicionar, width=30)
            entry_conta.pack()

            # Label e Entry para inserir o nome do titular
            label_nome = tk.Label(janela_adicionar, text="Digite o nome do titular:")
            label_nome.pack(pady=10)

            entry_nome = tk.Entry(janela_adicionar, width=30)
            entry_nome.pack()

            # Label e Entry para inserir a senha
            label_senha = tk.Label(janela_adicionar, text="Informe a senha da conta:")
            label_senha.pack(pady=10)

            entry_senha = tk.Entry(janela_adicionar, width=30, show="*")  # Mostra '*' no lugar da senha
            entry_senha.pack()

            # Botão para enviar dados
            btn_adicionar = tk.Button(janela_adicionar, text="Enviar Dados", command=pegar_valor)
            btn_adicionar.pack()

            janela_adicionar.mainloop()
                
        def on_verificar(): # Verificar conta
            data_transação = datetime.datetime.now()
            def pegar_valor():
                conta = entry_conta.get()
                senha = entry_senha.get()
                print(conta, senha)
                janela_adicionar.destroy()
                if conta and senha:
                    Banco.verificar_conta(conta, senha, data_transação)
                else:
                    print("Por favor, preencha todos os campos.")
            janela_adicionar = tk.Toplevel()
            janela_adicionar.title("Verificar Conta")

            # Label e Entry para inserir o número da conta
            label_conta = tk.Label(janela_adicionar, text="Insira o número da conta:")
            label_conta.pack(pady=10)

            entry_conta = tk.Entry(janela_adicionar, width=30)
            entry_conta.pack()

            # Label e Entry para inserira senha
            label_senha = tk.Label(janela_adicionar, text="Informe a senha da conta:")
            label_senha.pack()

            entry_senha = tk.Entry(janela_adicionar, width=30, show="*")
            entry_senha.pack()

            # Botão para enviar dados
            btn_adicionar = tk.Button(janela_adicionar, text="Enviar Dados", command=pegar_valor)
            btn_adicionar.pack()

            #Executar janela
            janela_adicionar.mainloop()

        def on_deposito(): # Realiza deposito
            data_transação = datetime.datetime.now()
            deposito_conta = input("Digite o número da conta para o depósito: ")
            try: 
                deposito_valor = float(input("Digite o valor do depósito: "))
            except ValueError:
                print("Valor inválido. Por favor, insira um valor númerico")
                root.mainloop() # volta ao inicio do loop
            if  deposito_valor <=0:
                print("O valor do depósito deve ser maior do que zero.")
                root.mainloop() # volta ao inicio do loop
            self.depositar(deposito_conta, deposito_valor, data_transação)

        def on_saque(): # Realizar saque
            data_transação = datetime.datetime.now()
            saque_numero_conta = input("Digite o número da conta para o saque: ")
            saque_senha = input(f"Digite a sua senha da conta {saque_numero_conta}: ")
            try: saque_valor = float(input("Digite o valor do saque: "))
            except ValueError: 
                print("Valor inválido. Por favor, insira um valor númerico")
                root.mainloop() # volta ao inicio do loop
            if saque_valor <=0:
                print("O valor do saque deve ser maior que zero.")
                root.mainloop() # volta ao inicio do loop
            self.saque(saque_numero_conta, saque_valor, saque_senha, data_transação)

        def on_transferencia(): # Realizar transferencia
            data_transação = datetime.datetime.now()
            numero_conta_pagadora = input("Digite o número da conta pagadora: ")
            senha_conta_pagadora = input(f"digite a senha da conta {numero_conta_pagadora}: ")
            numero_conta_recebedora = input("Digite o número da conta que irá receber: ")
            if numero_conta_pagadora != numero_conta_recebedora:
                try: valor_transferencia = float(input("Digite o valor da transferência: "))
                except ValueError:
                    print("O valor digitado é inválido")
                    root.mainloop() # volta ao inicio do loop
                if valor_transferencia <=0:
                    print("O valor da transferencia deve ser maior que zero.")
                    root.mainloop()
                self.transferencia(numero_conta_pagadora, numero_conta_recebedora, valor_transferencia, senha_conta_pagadora, data_transação)
            else:
                print("As contas não podem ser iguais.")

        def on_close():
            print("Encerrando o programa...")
            self.conexao.close()
            root.destroy()
            root.quit()
            sys.exit()

        #tkinter
        # Janela principal
        root = tk.Tk()
        root.title("Banco")

        # Criar um rótulo
        label = tk.Label(root, text=menu)
        label.pack(pady=10)

        # Criar um botão na janela
        button_adicionar = tk.Button(root,text="Adicionar Conta", command=on_adicionar)
        button_adicionar.pack(pady=10)

        button_verificar = tk.Button(root,text="Verificar Conta", command=on_verificar)
        button_verificar.pack(pady=10)

        button_deposito = tk.Button(root,text="Realizar Depósito", command=on_deposito)
        button_deposito.pack(pady=10)
            
        button_saque = tk.Button(root,text="Realizar Saque", command=on_saque)
        button_saque.pack(pady=10)

        button_transferencia = tk.Button(root,text="Realizar Transferência", command=on_transferencia)
        button_transferencia.pack(pady=10)

        button_saida = tk.Button(root,text="Encerrar Sistema", command=on_close)
        button_saida.pack(pady=10)

        root.mainloop()

if __name__ == "__main__":
    conexao = sqlite3.connect("Banco.db")
    Banco = Banco(conexao)
    Banco.menu_principal()