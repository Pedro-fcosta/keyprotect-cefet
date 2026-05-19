# Sistema de Controle de Chaves

Projeto desenvolvido para a disciplina **Projeto e Produto** do **CEFET/RJ**.

Este repositório contém um protótipo funcional de um sistema web para controle de retirada e devolução de chaves em um ambiente institucional.

---

## Sumário

- [Como editar este projeto usando Git e GitHub](#como-editar-este-projeto-usando-git-e-github)
- [Como rodar o projeto](#como-rodar-o-projeto)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Como editar partes específicas do sistema](#como-editar-partes-específicas-do-sistema)
- [Objetivo do projeto](#objetivo-do-projeto)
- [Funcionalidades](#funcionalidades)
- [Tecnologias utilizadas](#tecnologias-utilizadas)
- [Banco de dados](#banco-de-dados)
- [Exportação de dados](#exportação-de-dados)
- [Integrantes do grupo](#integrantes-do-grupo)
- [Professor](#professor)
- [Disciplina](#disciplina)
- [Instituição](#instituição)
- [Melhorias futuras](#melhorias-futuras)

---

# Como editar este projeto usando Git e GitHub

Esta parte é um passo a passo para os integrantes do grupo conseguirem baixar o projeto, editar arquivos e enviar alterações para o GitHub.

A ideia é que ninguém edite diretamente a branch principal sem organização. Cada integrante deve criar uma branch para sua tarefa, fazer as alterações, enviar para o GitHub e abrir um Pull Request.

---

## 1. Instalar o Git

Antes de começar, é necessário ter o Git instalado no computador.

Para verificar se já está instalado, abra o terminal, PowerShell ou Git Bash e digite:

```bash
git --version
```

Se aparecer uma versão, por exemplo:

```bash
git version 2.45.0
```

o Git já está instalado.

Se não aparecer, instale o Git pelo site oficial:

```text
https://git-scm.com/
```

Durante a instalação, pode manter as opções padrão.

---

## 2. Instalar o Visual Studio Code

O projeto pode ser editado em qualquer editor de código, mas a recomendação é usar o Visual Studio Code.

Baixe pelo site:

```text
https://code.visualstudio.com/
```

Depois de instalar, abra o VS Code e confira se consegue abrir pastas normalmente.

---

## 3. Clonar o repositório

Clonar significa baixar o projeto do GitHub para o seu computador.

Escolha uma pasta onde deseja salvar o projeto.

Exemplos:

```text
Documentos/
Área de Trabalho/
Projetos/
```

Dentro dessa pasta, clique com o botão direito e abra o terminal ou Git Bash.

Depois rode:

```bash
git clone LINK_DO_REPOSITORIO
```

Exemplo:

```bash
git clone https://github.com/usuario/sistema-controle-chaves.git
```

Depois entre na pasta do projeto:

```bash
cd sistema-controle-chaves
```

---

## 4. Abrir o projeto no VS Code

Com a pasta do projeto aberta no terminal, digite:

```bash
code .
```

Isso abrirá o projeto no Visual Studio Code.

Caso o comando `code .` não funcione, abra o VS Code manualmente e vá em:

```text
File > Open Folder
```

ou, em português:

```text
Arquivo > Abrir Pasta
```

Depois selecione a pasta do projeto.

---

## 5. Verificar em qual branch você está

Antes de começar qualquer edição, confira em qual branch você está:

```bash
git branch
```

A branch atual aparece com um asterisco `*`.

Exemplo:

```text
* main
```

A branch `main` é a branch principal do projeto.

---

## 6. Antes de editar, atualizar o projeto

Sempre antes de começar a mexer no projeto, vá para a branch `main`:

```bash
git checkout main
```

Depois rode:

```bash
git pull
```

Esse comando baixa as alterações mais recentes do GitHub.

Isso evita que você edite uma versão antiga do projeto.

---

## 7. Criar uma branch para sua alteração

Não é recomendado editar diretamente na branch `main`.

Crie uma branch com um nome relacionado à tarefa que você vai fazer.

Use:

```bash
git checkout -b nome-da-branch
```

Exemplos:

```bash
git checkout -b ajuste-readme
git checkout -b tela-dashboard
git checkout -b correcao-css
git checkout -b cadastro-usuarios
git checkout -b melhoria-historico
```

A partir desse momento, suas alterações ficam separadas da branch principal.

---

## 8. Editar os arquivos

Agora você pode editar os arquivos normalmente no VS Code.

Principais arquivos do projeto:

```text
app.py
```

Arquivo principal do sistema. Contém as rotas, regras de funcionamento, conexão com o banco de dados e lógica de cadastro, retirada, devolução, histórico e dashboard.

```text
templates/
```

Pasta com as páginas HTML do sistema.

```text
static/style.css
```

Arquivo responsável pelo visual do sistema: cores, tamanhos, cards, botões, tabelas e responsividade.

```text
static/logo-cefet.png
```

Imagem da logo usada no topo do sistema.

---

## 9. Rodar o sistema para testar antes de enviar

Antes de enviar qualquer alteração para o GitHub, rode o sistema e veja se ele continua funcionando.

Ative o ambiente virtual, caso esteja usando.

No Windows:

```bash
venv\Scripts\activate
```

No Linux/Mac:

```bash
source venv/bin/activate
```

Depois execute:

```bash
python app.py
```

Abra no navegador:

```text
http://127.0.0.1:5000
```

Teste a parte que você alterou.

Se o terminal mostrar erro, leia a mensagem e tente corrigir antes de enviar.

---

## 10. Ver quais arquivos foram alterados

Depois de editar, rode:

```bash
git status
```

Esse comando mostra quais arquivos foram modificados, adicionados ou removidos.

Exemplo de saída:

```text
modified:   templates/index.html
modified:   static/style.css
```

Isso significa que esses arquivos foram alterados.

---

## 11. Adicionar as alterações

Para adicionar todas as alterações feitas, use:

```bash
git add .
```

Se quiser adicionar apenas um arquivo específico:

```bash
git add nome_do_arquivo
```

Exemplos:

```bash
git add templates/index.html
git add static/style.css
```

---

## 12. Criar um commit

Commit é como salvar uma versão do projeto com uma mensagem explicando o que foi alterado.

Use:

```bash
git commit -m "Descrição da alteração"
```

Exemplos de boas mensagens:

```bash
git commit -m "Atualiza tela inicial"
git commit -m "Corrige layout do dashboard"
git commit -m "Adiciona instruções na README"
git commit -m "Melhora formulário de cadastro de chaves"
```

Evite mensagens genéricas como:

```bash
git commit -m "teste"
git commit -m "alterações"
git commit -m "coisas"
```

A mensagem deve explicar rapidamente o que foi feito.

---

## 13. Enviar a branch para o GitHub

Depois do commit, envie sua branch para o GitHub:

```bash
git push origin nome-da-branch
```

Exemplo:

```bash
git push origin ajuste-readme
```

Outro exemplo:

```bash
git push origin tela-dashboard
```

Se for a primeira vez enviando essa branch, esse comando cria a branch no GitHub.

---

## 14. Criar um Pull Request

Depois de enviar a branch, entre no GitHub pelo navegador.

O próprio GitHub normalmente mostrará uma opção chamada:

```text
Compare & pull request
```

Clique nela.

Depois preencha:

```text
Título: resumo da alteração
Descrição: o que foi feito
```

Exemplo de título:

```text
Ajuste na tela inicial
```

Exemplo de descrição:

```text
- Adiciona novo card no menu principal
- Ajusta texto dos botões
- Melhora espaçamento dos cards
```

Depois clique em:

```text
Create pull request
```

---

## 15. Revisar o Pull Request

Depois de criar o Pull Request, outro integrante do grupo pode revisar.

Na revisão, verifique:

- se o sistema continua rodando;
- se o arquivo correto foi alterado;
- se a alteração não quebrou outra parte;
- se não foram enviados arquivos desnecessários;
- se o código está compreensível.

---

## 16. Juntar a alteração com a main

Depois que o grupo revisar a alteração, o Pull Request pode ser aprovado.

Para juntar a alteração com a branch principal, clique em:

```text
Merge pull request
```

Depois clique em:

```text
Confirm merge
```

Pronto. A alteração passa a fazer parte da branch `main`.

---

## 17. Atualizar sua main depois do merge

Depois que um Pull Request for aceito, todos devem atualizar o projeto local.

Volte para a branch `main`:

```bash
git checkout main
```

Baixe as alterações:

```bash
git pull
```

Agora sua versão local estará atualizada.

---

## 18. Criar uma nova branch para a próxima tarefa

Sempre que for começar uma nova alteração, crie uma nova branch a partir da `main` atualizada:

```bash
git checkout main
git pull
git checkout -b nome-da-nova-tarefa
```

Exemplo:

```bash
git checkout -b ajuste-historico
```

---

## 19. Resumo do fluxo correto

Sempre que for editar o projeto, siga esta receita:

```bash
git checkout main
git pull
git checkout -b nome-da-tarefa
```

Edite os arquivos no VS Code.

Depois teste o sistema.

Em seguida:

```bash
git status
git add .
git commit -m "Descrição da alteração"
git push origin nome-da-tarefa
```

Depois, no GitHub:

```text
Criar Pull Request
Revisar
Fazer merge
```

---

## 20. Como resolver quando outra pessoa já alterou o projeto

Se alguém alterou o projeto antes de você, sempre atualize sua branch principal:

```bash
git checkout main
git pull
```

Depois crie sua branch novamente:

```bash
git checkout -b nome-da-tarefa
```

Se você já estava em uma branch antiga, pode atualizar sua branch com a main:

```bash
git checkout main
git pull
git checkout sua-branch
git merge main
```

Se houver conflito, o VS Code vai mostrar os arquivos com conflito.

Nesse caso, leia com cuidado, escolha quais alterações manter, salve o arquivo e depois rode:

```bash
git add .
git commit -m "Resolve conflitos com a main"
```

---

## 21. Como apagar uma branch local depois do merge

Depois que a branch já foi juntada na `main`, você pode apagar a branch local.

Primeiro vá para a main:

```bash
git checkout main
```

Depois apague a branch:

```bash
git branch -d nome-da-branch
```

Exemplo:

```bash
git branch -d ajuste-readme
```

Se o Git não permitir apagar, use:

```bash
git branch -D nome-da-branch
```

---

## 22. Como apagar uma branch do GitHub depois do merge

Para apagar uma branch remota:

```bash
git push origin --delete nome-da-branch
```

Exemplo:

```bash
git push origin --delete ajuste-readme
```

---

## 23. O que não fazer

Evite:

- editar direto na branch `main`;
- fazer alterações sem antes rodar `git pull`;
- subir arquivos desnecessários, como `venv/` e `__pycache__/`;
- apagar arquivos sem avisar o grupo;
- mudar nomes de arquivos importantes sem necessidade;
- fazer commits com mensagens genéricas como `teste`, `alteração` ou `coisas`;
- enviar código sem testar;
- alterar campos `name=""` no HTML sem alterar também no `app.py`;
- apagar o banco de dados sem avisar o grupo.

---

## 24. Arquivos que normalmente não devem ser enviados

Evite enviar para o GitHub:

```text
venv/
__pycache__/
*.pyc
.env
```

Esses arquivos devem ficar no `.gitignore`.

Exemplo de `.gitignore`:

```gitignore
__pycache__/
*.pyc
venv/
.venv/
.env
.DS_Store
```

Caso o banco tenha dados reais de pessoas, também é melhor ignorar:

```gitignore
database.db
exports/
```

---

# Como rodar o projeto

Esta parte mostra como executar o sistema no computador.

---

## 1. Criar ambiente virtual

Na pasta do projeto, rode:

No Windows:

```bash
python -m venv venv
```

No Linux/Mac:

```bash
python3 -m venv venv
```

---

## 2. Ativar o ambiente virtual

No Windows:

```bash
venv\Scripts\activate
```

No Linux/Mac:

```bash
source venv/bin/activate
```

Quando o ambiente virtual estiver ativado, normalmente aparece algo como `(venv)` no terminal.

---

## 3. Instalar o Flask

Com o ambiente virtual ativado, instale o Flask:

```bash
pip install flask
```

---

## 4. Rodar o sistema

Execute:

```bash
python app.py
```

Depois abra no navegador:

```text
http://127.0.0.1:5000
```

Se tudo estiver correto, a tela inicial do sistema será aberta.

---

## 5. Parar o sistema

Para parar o Flask, volte ao terminal e pressione:

```text
CTRL + C
```

---

# Estrutura do projeto

A estrutura básica do projeto é:

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
```

---

# Como editar partes específicas do sistema

Esta parte explica onde mexer caso alguém queira alterar alguma parte do sistema.

---

## Editar o visual

O visual fica no arquivo:

```text
static/style.css
```

Nesse arquivo é possível alterar:

- cores;
- tamanho da logo;
- espaçamentos;
- cards;
- botões;
- tabelas;
- responsividade;
- tamanho das fontes;
- efeitos de hover.

Exemplo de variáveis de cor:

```css
:root {
    --azul-principal: #0b3d91;
    --azul-escuro: #082d6b;
    --azul-claro: #eaf1fb;
}
```

Para mudar a cor principal, altere o valor de:

```css
--azul-principal
```

---

## Editar a logo

A logo fica na pasta:

```text
static/
```

O arquivo usado no sistema é:

```text
logo-cefet.png
```

Para trocar a logo:

1. Coloque a nova imagem dentro da pasta `static`.
2. Renomeie a imagem para `logo-cefet.png`.
3. Rode novamente o Flask, se necessário.

A logo é chamada no arquivo:

```text
templates/base.html
```

Neste trecho:

```html
<img src="{{ url_for('static', filename='logo-cefet.png') }}" alt="Logo CEFET/RJ" class="logo-img">
```

---

## Editar o menu

O menu principal fica no arquivo:

```text
templates/base.html
```

Procure a parte:

```html
<nav class="menu">
```

Exemplo:

```html
<nav class="menu">
    <a href="{{ url_for('index') }}">Início</a>
    <a href="{{ url_for('retirada') }}">Retirada</a>
    <a href="{{ url_for('devolucao') }}">Devolução</a>
    <a href="{{ url_for('chaves') }}">Chaves</a>
    <a href="{{ url_for('usuarios') }}">Usuários</a>
    <a href="{{ url_for('historico') }}">Histórico</a>
    <a href="{{ url_for('dashboard') }}">Dashboard</a>
</nav>
```

Para adicionar um novo botão no menu, adicione uma nova linha:

```html
<a href="{{ url_for('nome_da_rota') }}">Nome da Página</a>
```

A rota precisa existir no arquivo `app.py`.

---

## Editar a tela inicial

A tela inicial fica em:

```text
templates/index.html
```

Nela estão:

- cards de resumo;
- botões principais;
- atalhos para as páginas do sistema.

Exemplo de card de ação:

```html
<a class="acao" href="{{ url_for('retirada') }}">
    <h3>Retirar chave</h3>
    <p>Registre a retirada de uma chave disponível.</p>
</a>
```

Você pode alterar o título dentro de `<h3>` e a descrição dentro de `<p>`.

---

## Editar as páginas HTML

Cada página fica dentro da pasta `templates`.

| Tela | Arquivo |
|---|---|
| Tela inicial | `index.html` |
| Base visual do sistema | `base.html` |
| Cadastro de chaves | `cadastrar_chave.html` |
| Consulta de chaves | `chaves.html` |
| Cadastro de usuários | `cadastrar_usuario.html` |
| Consulta de usuários | `usuarios.html` |
| Retirada de chave | `retirada.html` |
| Devolução de chave | `devolucao.html` |
| Histórico | `historico.html` |
| Dashboard | `dashboard.html` |

---

## Editar as rotas

As rotas ficam no arquivo:

```text
app.py
```

Exemplo de rota:

```python
@app.route("/chaves")
def chaves():
    return render_template("chaves.html")
```

Isso significa que o endereço:

```text
/chaves
```

abre o arquivo:

```text
templates/chaves.html
```

---

## Adicionar uma nova página

Para criar uma nova página, siga estes passos.

### 1. Criar a rota no `app.py`

Exemplo:

```python
@app.route("/sobre")
def sobre():
    return render_template("sobre.html")
```

### 2. Criar o arquivo HTML

Dentro da pasta `templates`, crie:

```text
sobre.html
```

Exemplo:

```html
{% extends "base.html" %}

{% block title %}Sobre | Controle de Chaves{% endblock %}

{% block content %}

<section class="titulo-pagina">
    <h2>Sobre o sistema</h2>
    <p>Informações sobre o projeto.</p>
</section>

<section class="form-box">
    <p>Este sistema foi desenvolvido para a disciplina Projeto e Produto.</p>
</section>

{% endblock %}
```

### 3. Adicionar a página no menu

No arquivo:

```text
templates/base.html
```

adicione dentro do menu:

```html
<a href="{{ url_for('sobre') }}">Sobre</a>
```

---

## Editar campos de formulário

Os campos dos formulários ficam nos arquivos HTML dentro da pasta `templates`.

Exemplo em um formulário:

```html
<div class="campo">
    <label for="codigo">Código da chave</label>
    <input type="text" id="codigo" name="codigo" placeholder="Ex: CH-001" required>
</div>
```

Atenção ao atributo:

```html
name="codigo"
```

Esse nome é usado no `app.py`.

Exemplo:

```python
codigo = request.form["codigo"].strip()
```

Se mudar o `name` no HTML, precisa mudar também no Python.

---

# Objetivo do projeto

O objetivo do projeto é desenvolver um protótipo funcional para controlar a retirada e devolução de chaves em um ambiente institucional.

O sistema busca resolver problemas como:

- falta de registro confiável de retirada de chaves;
- dificuldade para saber quem está com determinada chave;
- ausência de histórico organizado;
- dificuldade para identificar chaves não devolvidas;
- controle manual sujeito a erros;
- dificuldade para consultar dados antigos;
- ausência de indicadores de uso.

---

# Funcionalidades

O sistema possui:

- cadastro de usuários;
- cadastro de chaves;
- registro de retirada de chaves;
- registro de devolução de chaves;
- consulta de chaves cadastradas;
- consulta de usuários cadastrados;
- histórico de movimentações;
- busca no histórico;
- dashboard com indicadores;
- exportação do histórico em CSV;
- indicador da chave há mais tempo sem devolução;
- atualização automática do status da chave;
- banco de dados local em SQLite.

---

# Tecnologias utilizadas

O projeto utiliza:

- Python;
- Flask;
- SQLite;
- HTML;
- CSS;
- Git;
- GitHub.

---

# Banco de dados

O projeto usa SQLite.

O arquivo do banco é:

```text
database.db
```

As tabelas principais são:

```text
usuarios
chaves
movimentacoes
```

---

## Tabela `usuarios`

Guarda os dados dos usuários autorizados a retirar chaves.

Campos principais:

```text
id
matricula
nome
curso_setor
telefone
criado_em
```

---

## Tabela `chaves`

Guarda os dados das chaves cadastradas.

Campos principais:

```text
id
codigo
local
descricao
status
criado_em
```

---

## Tabela `movimentacoes`

Guarda as retiradas e devoluções.

Campos principais:

```text
id
usuario_id
chave_id
data_retirada
data_devolucao
status
observacao
```

---

# Como resetar o banco de dados

Para apagar todos os dados e começar de novo:

1. Pare o Flask no terminal usando `CTRL + C`.
2. Apague o arquivo:

```text
database.db
```

3. Rode novamente:

```bash
python app.py
```

O sistema criará um banco novo automaticamente.

Atenção: isso apaga todos os usuários, chaves e movimentações cadastradas.

---

# Exportação de dados

O sistema permite exportar o histórico de movimentações em CSV.

A exportação fica disponível na tela:

```text
/historico
```

Clique no botão:

```text
Exportar CSV
```

O sistema gera o arquivo:

```text
historico_chaves.csv
```

Dentro da pasta:

```text
exports/
```

Esse arquivo pode ser aberto no Excel, LibreOffice Calc ou em ferramentas de análise de dados.

---

# Integrantes do grupo

Preencher com os nomes dos integrantes:

```text
Nome 1 -
Nome 2 -
Nome 3 -
Nome 4 -
Nome 5 -
```

---

# Professor

Preencher com o nome do professor:

```text
Professor: HARON CALEGARI FANTICELLI
```

---

# Disciplina

```text
Projeto e Produto
```

---

# Instituição

```text
CEFET/RJ
```

---

# Melhorias futuras

Algumas melhorias possíveis:

- edição de chaves cadastradas;
- edição de usuários cadastrados;
- exclusão segura de registros;
- login por usuário;
- níveis de acesso;
- filtro por período no histórico;
- relatório específico de pendências;
- backup do banco de dados;
- integração com QR Code;
- versão otimizada para tablet ou celular;
- dashboard com gráficos;
- geração de relatórios em PDF;
- envio de alerta para chaves não devolvidas;
- cadastro de responsáveis por setor;
- controle de autorização por tipo de usuário.
