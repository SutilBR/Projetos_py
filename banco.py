import datetime
import sqlite3
import hashlib
import secrets
import tkinter as tk
from tkinter import messagebox
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
            messagebox.showerror("Conta já existe", f"A conta {numero_conta} já existe no sistema.")
        else: # Cria a conta e adiciona o histórico dela
            # Gerar o hash dasenha e o salt
            hash_senha, salt = self.hash_senha(senha)
            # Historico
            self.historico(numero_conta, "Conta criada", 0, True, data)
            self.historico_cadastro(numero_conta, detalhe_conta["nome_titular"], hash_senha, salt, data)
            messagebox.showinfo("Conta adicionada", f"A conta {numero_conta} foi adicionada com sucesso")
    
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
            if self.verificar_senha(numero_conta, senha):
                saldo = self.obter_saldo_atual(numero_conta)
                messagebox.showinfo("Saldo Atual", f"Seu saldo é de R$ {saldo:.2f}")
                self.historico(numero_conta, "Conta verificada", saldo, True, data)
            else:
                messagebox.showerror("Senha Incorreta", "Senha fornecida incorreta. Por favor, tente novamente")
        else: # a conta não existe, e dá a opção de criar uma nova conta
            messagebox.showerror("Conta não encontrada",f"A conta {numero_conta} não foi encontrada.\nSe você deseja criar uma nova conta, por favor clique em 'Adicionar Conta' no menu principal.")

    def depositar(self, numero_conta, valor, data):
        """
        Função para realizar o depósito, é verificado se a conta existe

        Args:
            numero_conta: numero da conta
            valor: valor do depósito
            data: data
        """
        if valor  <= 0:
            messagebox.showerror("Valor inválido", "O valor do depósito  deve ser maior que zero.")
            return
        saldo = self.obter_saldo_atual(numero_conta)
        saldo = saldo + valor
        self.historico(numero_conta, "Depósito", saldo, True, data)
        messagebox.showinfo("Depósito Realizado", f"Depósito de R$ {valor:.2f} realizado com sucesso. Novo saldo:R$ {saldo:.2f}")

    def transferencia(self, numero_conta_pagadora, numero_conta_recebedora, valor, senha, data):
        """
        Função para realizar transferencia entre contas existentes

        Args:
            numero_conta_recebedora: numero da conta que irá receber o dinheiro
            numero_conta_pagadora: numero da conta que irá pagar
            valor: valor da transferencia
            data: data da transação
        """
        if numero_conta_pagadora == numero_conta_recebedora:
            messagebox.showerror("Erro na transferência", "As contas de origem e destino não podem ser iguais.")
            return
        if valor <= 0:
            messagebox.showerror("Valor inválido", "O valor datransferência deve ser maior do que zero")
            return

        if not self.verificar_senha(numero_conta_pagadora, senha):
            messagebox.showerror("Senha incorreta", "Senha fornecida incorreta. Por favor, tente novamente")
            return
        
        saldo = self.obter_saldo_atual(numero_conta_pagadora)
        if saldo < valor:
            messagebox.showerrors("Saldo Insuficiente", f"Saldo Insuficiente para transferência. Saldo atual: R${saldo:.2f}")
            self.historico(numero_conta_pagadora, "Transferencia Débito", saldo, False, data)
            return

        saldo_destino = self.obter_saldo_atual(numero_conta_recebedora)
        saldo = saldo - valor
        saldo_destino = saldo_destino + valor
        self.historico(numero_conta_pagadora, "Transferencia Débito", saldo, True, data)
        self.historico(numero_conta_recebedora, "Transferencia Crédito", saldo_destino, True, data)
        messagebox.showinfo("Transferência Realizada", f"Transferência de R$ {valor:.2f} realizada com sucesso. Seu saldo é de R$ {saldo:.2f}.")

    def saque(self, numero_conta, valor, senha, data):
        """
        Realiza o saque, verifica se na conta existe saldo e faz o saque. mostra o novo valor do saldo após o saque

        Args:
            numero_conta: numero da conta
            valor: valor do saque
            data: data
        """

        if valor <= 0:
            messagebox.showerror("Valor Inválido", "O valor do saque deve ser maior que zero.")
            return
        
        if not self.verificar_senha(numero_conta, senha):
            messagebox.showerror("Senha Incorreta", "Senha fornecida incorreta. Por favor, tente novamente.")
            return

        saldo_atual = self.obter_saldo_atual(numero_conta)
        if saldo_atual < valor:
            messagebox.showerror("Saldo Insuficiente", f"Saldo insuficiente para saque. Saldo atual: R$ {saldo_atual:.2f}")
            self.historico(numero_conta, "Saque", saldo_atual, False, data)
            return

        novo_saldo = saldo_atual - valor
        self.historico(numero_conta, "Saque", novo_saldo, True, data)
        messagebox.showinfo("Saque Realizado", f"Saque de R$ {valor:.2f} realizado com sucesso. Novo saldo: R$ {novo_saldo:.2f}")

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

    def obter_saldo_atual(self, numero_conta):
        self.cursor.execute("SELECT Saldo FROM historico WHERE Numero_conta = ? ORDER BY id DESC LIMIT 1", (numero_conta,))
        resultado = self.cursor.fetchone()
        if resultado:
            return resultado[0]
        return 0.0
    
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
                    messagebox.showerror("Erro tente novamente", "Por favor preenhca todos os campos e tente novamente.")
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
                janela_adicionar.destroy()
                if conta and senha:
                    Banco.verificar_conta(conta, senha, data_transação)
                else:
                    messagebox.showerror("Erro, tente novamente", "Selecione a opção desejada e tente novamente, certifique-se de preencher todas as informações")
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
            def pegar_valor():
                conta = entry_conta.get()
                valor_banco = entry_valor.get()
                janela_adicionar.destroy()
                if conta:
                    try:
                        valor_banco = float(valor_banco)
                    except ValueError:
                        messagebox.showerror("Erro, tente novamente", "O valor informado não corresponde um valor númerico.")
                        return
                    if valor_banco <=0:
                        messagebox.showerror("Erro, tente novamente", "O valor informado deve ser maior do que zero.")
                        return
                    self.depositar(conta, valor_banco, data_transação)

            janela_adicionar = tk.Toplevel()
            janela_adicionar.title("Realizar Depósito")
            # Label e Entry para inserir o número da conta
            label_conta = tk.Label(janela_adicionar, text="Insira o número da conta:")
            label_conta.pack(pady=10)
            entry_conta = tk.Entry(janela_adicionar, width=30)
            entry_conta.pack()
            # Label e Entry para inerir o valor
            label_valor = tk.Label(janela_adicionar, text="Insira o valor do depósito:")
            label_valor.pack(pady=10)
            entry_valor = tk.Entry(janela_adicionar, width=30)
            entry_valor.pack()
            # Botão para enviar dados
            btn_adicionar = tk.Button(janela_adicionar, text="Enviar Dados", command=pegar_valor)
            btn_adicionar.pack()
            
            janela_adicionar.mainloop()

        def on_saque(): # Realizar saque
            data_transação = datetime.datetime.now()
            def pegar_valor():
                conta = entry_conta.get()
                valor_banco = entry_valor.get()
                senha = entry_senha.get()
                janela_adicionar.destroy()
                if conta and senha:
                    try:
                        valor_banco = float(valor_banco)
                    except ValueError:
                        messagebox.showerror("Erro, tente novamente", "O valor informado não corresponde um valor númerico.")
                        return
                    if valor_banco <=0:
                        messagebox.showerror("Erro, tente novamente", "O valor informado deve ser maior do que zero.")
                        return
                    self.saque(conta, valor_banco, senha, data_transação)

            janela_adicionar = tk.Toplevel()
            janela_adicionar.title("Realizar Saque")
            # Label e Entry para inserir o número da conta
            label_conta = tk.Label(janela_adicionar, text="Insira o número da conta:")
            label_conta.pack(pady=10)
            entry_conta = tk.Entry(janela_adicionar, width=30)
            entry_conta.pack()
            # Label e Entry para inserir a senha
            label_senha = tk.Label(janela_adicionar, text="Insira a senha:")
            label_senha.pack(pady=10)
            entry_senha = tk.Entry(janela_adicionar, width=30, show="*")
            entry_senha.pack()
            # Label e Entry para inerir o valor
            label_valor = tk.Label(janela_adicionar, text="Insira o valor do Saque:")
            label_valor.pack(pady=10)
            entry_valor = tk.Entry(janela_adicionar, width=30)
            entry_valor.pack()
            # Botão para enviar dados
            btn_adicionar = tk.Button(janela_adicionar, text="Enviar Dados", command=pegar_valor)
            btn_adicionar.pack()
            
            janela_adicionar.mainloop()

        def on_transferencia(): # Realizar transferencia
            data_transação = datetime.datetime.now()
            def pegar_valor():
                conta = entry_conta.get()
                valor_banco = entry_valor.get()
                senha = entry_senha.get()
                conta_destino = entry_destino.get()
                janela_adicionar.destroy()
                if conta and senha and conta_destino:
                    try:
                        valor_banco = float(valor_banco)
                    except ValueError:
                        messagebox.showerror("Erro, tente novamente", "O valor informado não corresponde um valor númerico.")
                        return
                    if valor_banco <= 0:
                        messagebox.showerror("Erro, tente novamente", "O valor informado deve ser maior do que zero.")
                        return
                    self.transferencia(conta, conta_destino, valor_banco, senha, data_transação)

            janela_adicionar = tk.Toplevel()
            janela_adicionar.title("Realizar Transferência")
            # Label e Entry para inserir o número da conta
            label_conta = tk.Label(janela_adicionar, text="Insira o número da conta:")
            label_conta.pack(pady=10)
            entry_conta = tk.Entry(janela_adicionar, width=30)
            entry_conta.pack()
            # Label e Entry para inserir a senha e a conta destino
            label_senha = tk.Label(janela_adicionar, text="Insira a senha:")
            label_senha.pack(pady=10)
            entry_senha = tk.Entry(janela_adicionar, width=30, show="*")
            entry_senha.pack()
            label_destino = tk.Label(janela_adicionar, text="Insira o número da conta de destino:")
            label_destino.pack(pady=10)
            entry_destino = tk.Entry(janela_adicionar, width=30)
            entry_destino.pack()
            # Label e Entry para inerir o valor
            label_valor = tk.Label(janela_adicionar, text="Insira o valor da Transferência:")
            label_valor.pack(pady=10)
            entry_valor = tk.Entry(janela_adicionar, width=30)
            entry_valor.pack()
            # Botão para enviar dados
            btn_adicionar = tk.Button(janela_adicionar, text="Enviar Dados", command=pegar_valor)
            btn_adicionar.pack()
            
            janela_adicionar.mainloop()
        def on_close():
            messagebox.showwarning("Encerrando o sistema","Encerrando o sistema, obrigado pela preferência")
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