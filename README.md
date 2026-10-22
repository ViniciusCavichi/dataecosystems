# Essência — gestão para clínica de estética

Aplicação local em português com agenda, cadastro de clientes e prontuários de evolução. Interface em bege e marrom, adaptada para computador e celular.

## Executar

Requer **Python 3.10 ou superior**, sem dependências externas:

```bash
cd /workspace/dataecosystems
python3 app.py
```

No seu computador, execute o comando na pasta do projeto e abra **http://127.0.0.1:8000**. Para encerrar, pressione `Ctrl+C`. No Windows, pode usar `py app.py`.

O banco SQLite é criado automaticamente em `data/clinica.db` e os dados persistem após reiniciar. A aplicação funciona sem internet e utiliza fontes disponíveis no computador. Para outra porta, use `PORT=8001 python3 app.py` (Linux/macOS).

## Fluxo de uso

1. Cadastre o cliente com nome, endereço, idade, e-mail, telefone, Instagram e observações.
2. Agende o procedimento com data, horário, duração e status. A agenda considera uma profissional/sala e impede sobreposição de horários, exceto agendamentos cancelados.
3. Em Prontuários, selecione o paciente e registre procedimento, evolução e orientações. A linha do tempo permite consultar, editar e excluir registros mediante confirmação.
4. Atualize o status dos agendamentos conforme o atendimento: Agendado, Confirmado, Concluído ou Cancelado.

Datas e horários são os do computador, sem conversão de fuso. A idade é informada manualmente. Não há dados fictícios na base inicial.

## Dados e limites desta versão

A aplicação escuta apenas em `127.0.0.1`, para uso no próprio computador. Esta versão não tem autenticação, criptografia do banco nem controle de acesso por profissional. Não exponha o servidor na internet. Para uso clínico real, proteja o acesso ao computador e avalie controles de acesso e requisitos de proteção dos prontuários antes de cadastrar dados sensíveis.

Para fazer backup, **pare a aplicação** e copie `data/clinica.db` para um local protegido. Para restaurar, pare a aplicação e substitua o arquivo pelo backup. O banco não é versionado no Git. `CLINICA_DB` permite escolher outro caminho para o banco.

## Validar

```bash
python3 -m unittest discover -s tests -v
```

Os testes utilizam banco temporário separado, sem alterar dados reais.
