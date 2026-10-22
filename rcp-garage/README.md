# RCP Garage — fabricação e manutenção de triciclos

Projeto independente da aplicação Essência. Interface preta e vermelha, com tela de entrada e botão Acessar. Funciona offline no computador, com Python 3.10+ e sem instalação de bibliotecas.

## Windows

1. Instale Python de https://www.python.org/downloads/windows/ e marque **Add python.exe to PATH**.
2. Extraia todo o ZIP, abra a pasta **RCP-Garage** e dê dois cliques em **INICIAR.bat**.
3. Mantenha a janela aberta enquanto utiliza o sistema. O navegador abre automaticamente.
4. Para encerrar, feche a janela ou pressione Ctrl+C. Para voltar, abra INICIAR.bat.

No terminal: `python app.py`. Endereço: http://127.0.0.1:8001. Não conflita com a clínica, que usa porta 8000.

## Começar

- **Dados da oficina:** preencha nome, CNPJ/CPF, endereço, telefone e e-mail para inclusão no PDF. Carregue a imagem original da logo (PNG/JPEG/WebP, até 2 MB). Até isso ser feito, é usada uma identificação vetorial provisória. A logo aparece na entrada e no menu; o PDF usa cabeçalho em texto com identidade vermelha.
- **Clientes:** nome, idade, endereço, telefone, e-mail, Instagram e observações.
- **Veículos:** modelo/identificação, cliente proprietário, placa, ano, chassi, cor e observações. Veículos sem placa também são aceitos.
- **Planejador:** tarefas internas ou vinculadas ao cliente e veículo, data, horário opcional, prioridade normal/alta/entrega, descrição e etapas A fazer, Em andamento, Concluída e Cancelada. Visões do dia, dos próximos 7 dias e de todas as tarefas. Tarefas paralelas são permitidas. Não gera tarefas recorrentes automaticamente.
- **Orçamentos:** cliente, veículo opcional, emissão, validade, situação e itens com descrição, quantidade, valor unitário e subtotal. Total calculado no servidor em centavos, sem impostos ou descontos automáticos. Use as observações para pagamento, prazo e condições. Salve e clique **PDF** para baixar um documento A4 com várias páginas quando necessário, dados da oficina, cliente e veículo, itens e total. Não depende de imprimir pelo navegador.

As datas são locais e a idade é informada manualmente. O botão Acessar é uma tela de apresentação, não uma autenticação. Edições alteram os dados atuais; não há histórico de versões de orçamentos nem assinatura digital. O PDF usa os dados atuais da oficina/cliente/veículo; guarde a cópia enviada ao cliente. Caracteres fora do alfabeto ocidental padrão podem ser substituídos no PDF.

## Dados e backup

O banco SQLite independente fica em **data/garage.db**, criado na primeira execução. Ele não é enviado ao GitHub nem incluído no ZIP. Para backup, encerre a aplicação e copie o banco para um local protegido. Para restaurar, encerre e substitua o arquivo pelo backup. A logo configurada fica armazenada no banco. Nunca substitua essa pasta ao atualizar o programa.

O servidor aceita somente conexões locais (127.0.0.1). Não tem login nem criptografia em repouso: proteja o acesso ao computador e não exponha o servidor na internet. RCP_DB permite alterar o caminho do banco e PORT permite alterar a porta. Não apague cadastros com vínculos: o sistema impede a exclusão para preservar os registros. Veículos com tarefas ou orçamentos não podem trocar de proprietário.

## Validação

Na pasta do projeto: `python -m unittest discover -s tests -v`. Testes usam banco temporário, sem dados reais.
