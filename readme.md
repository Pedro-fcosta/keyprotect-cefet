# Sistema de Controle de Chaves

Projeto desenvolvido para a disciplina **Projeto e Produto** do **CEFET/RJ**.

O objetivo do sistema é controlar a retirada e devolução de chaves em um ambiente institucional, registrando responsáveis, horários de retirada, devolução, pendências e histórico de movimentações.

---

## Tecnologias utilizadas

- Python
- Flask
- SQLite
- HTML
- CSS
- CSV para exportação de dados

---

## Funcionalidades

O sistema permite:

- Cadastrar usuários
- Cadastrar chaves
- Registrar retirada de chaves
- Registrar devolução de chaves
- Consultar chaves cadastradas
- Consultar usuários cadastrados
- Visualizar histórico de movimentações
- Filtrar movimentações
- Visualizar dashboard com indicadores
- Exportar histórico em CSV
- Identificar a chave há mais tempo sem devolução

---

## Estrutura do projeto

```text
controle_chaves_cefet/
│
├── app.py
├── database.db
├── README.md
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── cadastrar_chave.html
│   ├── chaves.html
│   ├── cadastrar_usuario.html
│   ├── usuarios.html
│   ├── retirada.html
│   ├── devolucao.html
│   ├── historico.html
│   └── dashboard.html
│
├── static/
│   ├── style.css
│   └── logo-cefet.png
│
└── exports/
    └── historico_chaves.csv