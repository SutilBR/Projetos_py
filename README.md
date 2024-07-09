# Aplicativo Bancário em Python
Este é um simples aplicativo bancário desenvolvido em Python utilizando Tkinter para a interface gráfica e SQLite para o armazenamento de dados. O aplicativo permite realizar operações bancárias básicas como criar contas, verificar saldo, realizar depósitos, saques e transferências entre contas.

### Requisitos
- Python 3.x
- Tkinter (geralmente já incluído na instalação padrão do Python)
- SQLite3

### Instalação
Clone o repositório:
``` git clone https://github.com/SutilBR/Projetos_py.git ```
``` cd seu-repositorio ```

Instale as dependências:
Certifique-se de ter o Python 3.x instalado. Para instalar as dependências necessárias (se ainda não estiverem instaladas), execute:
``` pip install tkinter sqlite3 ```

### Como Usar
Execute o aplicativo:
No terminal, navegue até o diretório onde o código está localizado e execute:
``` python Banco.py ```
Isso abrirá a interface do aplicativo bancário.

Opções Disponíveis:

- Adicionar Conta: Crie uma nova conta bancária fornecendo o número da conta, nome do titular e senha.
- Verificar Conta: Verifique o saldo de uma conta existente inserindo o número da conta e a senha.
- Realizar Depósito: Adicione fundos a uma conta existente fornecendo o número da conta e o valor a ser depositado.
- Realizar Saque: Retire fundos de uma conta existente inserindo o número da conta, senha e valor a ser sacado.
- Realizar Transferência: Transfira fundos entre duas contas existentes fornecendo o número da conta de origem, número da conta de destino, senha e valor a ser transferido.
- Encerrar Sistema: Fecha o aplicativo.

### Notas Adicionais
Certifique-se de que todas as informações fornecidas durante as operações (como número da conta, nome do titular e senhas) sejam corretas para evitar erros.
Os registros de todas as transações são armazenados localmente no banco de dados SQLite (Banco.db).
