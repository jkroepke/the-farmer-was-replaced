# The Farmer Was Replaced — Scripts das Turmas

Neste repositório ficam os scripts Python que vocês vão criar para controlar o fazendeiro no jogo **The Farmer Was Replaced**.

---

## Como funciona

O jogo interpreta arquivos `.py` que ficam dentro da pasta da sua turma, dentro de `Saves/`:

- `Saves/8h/` → turma das 8h
- `Saves/10h/` → turma das 10h
- `Saves/12h/` → turma das 12h
- `Saves/14h/` → turma das 14h

Cada aluno cria **seu próprio arquivo** dentro da pasta da turma. O nome do arquivo deve ser **seu nome completo, em letras minúsculas, sem acento, com `_` separando as palavras**, por exemplo:

```
joao silva         → joao_silva.py
Maria Fernández    → maria_fernandez.py
Ana Beatriz Souza  → ana_beatriz_souza.py
```

---

## Passo a passo para enviar seu script

### 1. Verifique se o Git está instalado

O Git provavelmente já está instalado no computador da escola. Para confirmar, abra o **Git Bash** (procure no menu Iniciar) ou um terminal e rode:

```bash
git --version
```

Se aparecer um número de versão, está tudo certo. Caso contrário, baixe em [https://git-scm.com](https://git-scm.com) e instale com as opções padrão.

### 2. Configure seu nome e e-mail (só na primeira vez)

Abra o **Git Bash** (ou o terminal) e rode:

```bash
git config --global user.name "Seu Nome Completo"
git config --global user.email "seu@email.com"
```

### 3. Clone o repositório

```bash
git clone <URL_DO_REPOSITORIO>
```

Substitua `<URL_DO_REPOSITORIO>` pelo endereço que o professor passar. Isso vai criar uma pasta no seu computador com todos os arquivos.

### 4. Entre na pasta do repositório

```bash
cd TheFarmerWasReplaced
```

### 5. Abra a pasta no VS Code e crie seu arquivo Python

O **VS Code** (Visual Studio Code) é o editor que vamos usar para escrever o código. Ele provavelmente já está instalado no computador da escola. Procure por **Visual Studio Code** no menu Iniciar.

> Caso não esteja instalado, baixe em [https://code.visualstudio.com](https://code.visualstudio.com) e instale com as opções padrão.

**Abrindo a pasta do repositório no VS Code:**

1. Abra o VS Code
2. Vá em **File → Open Folder** (ou `Ctrl+K` depois `Ctrl+O`)
3. Navegue até a pasta `TheFarmerWasReplaced` que foi criada quando você clonou o repositório e clique em **Selecionar Pasta**

Você vai ver a estrutura de pastas no painel esquerdo.

**Criando seu arquivo:**

1. No painel esquerdo, clique na pasta da sua turma (`8h`, `10h`, `12h` ou `14h`) para expandi-la
2. Clique no ícone de **novo arquivo** (aparece quando você passa o mouse sobre a pasta) — ou clique com o botão direito na pasta e escolha **New File**
3. Digite o nome do arquivo com seu nome completo, em minúsculo, sem acento, com `_` separando as palavras, terminando em `.py`  
   Exemplo: `joao_silva.py`
4. Pressione `Enter`

O arquivo vai abrir automaticamente para edição. Escreva seu código e salve com `Ctrl+S`.

Exemplo de conteúdo mínimo:

```python
while True:
    if can_harvest():
        harvest()
```

**Abrindo o terminal dentro do VS Code:**

Em vez de abrir o Git Bash separado, você pode usar o terminal integrado do VS Code:

- Vá em **Terminal → New Terminal** (ou `Ctrl+` `` ` ``)
- O terminal já abre na pasta certa, pronto para os próximos passos

### 6. Adicione o arquivo ao Git

```bash
git add Saves/10h/seu_nome.py
```

(troque `10h` pela pasta da sua turma e `seu_nome.py` pelo nome correto do seu arquivo)

### 7. Crie um commit

```bash
git commit -m "add seu_nome"
```

### 8. Envie para o repositório

```bash
git push
```

Se for a primeira vez, o Git pode pedir seu usuário e senha do GitHub (ou um token de acesso pessoal).

---

## Regras importantes

> **O Git registra permanentemente o autor de cada alteração.** O professor consegue ver exatamente quem modificou qual arquivo e quando. Qualquer aluno que alterar o arquivo de outro colega será penalizado.

- Mexa **somente no seu próprio arquivo**.
- Não altere arquivos de outros alunos, de outras turmas, nem arquivos de configuração do jogo.
- Se der erro no `git push`, avise o professor.
- Você pode fazer `git push` várias vezes — cada envio atualiza seu script.

---

## Referência rápida dos comandos do jogo

| Comando | O que faz |
|---|---|
| `harvest()` | Colhe o item na célula atual |
| `can_harvest()` | Retorna `True` se tem algo para colher |
| `move(Norte/Sul/Leste/Oeste)` | Move o fazendeiro |
| `plant(Entities.Wheat)` | Planta trigo na célula atual |
| `till()` | Ara o solo |
| `get_pos_x()` / `get_pos_y()` | Posição atual do fazendeiro |

Consulte a aba de ajuda dentro do jogo para a lista completa de comandos.
