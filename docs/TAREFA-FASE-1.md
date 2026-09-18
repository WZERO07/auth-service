# Tarefa: Serviço de Autenticação com FastAPI — Fase 1

> **Para:** Wendel
> **De:** Bruno
> **Projeto:** `auth-service`
> **Status:** Aberta
> 
---

## Contexto do projeto

Estamos construindo um serviço de autenticação do zero, em camadas. A ideia é
evoluir o projeto por fases, adicionando uma responsabilidade nova de cada vez.
Assim você aprende (e a gente revisa) um conceito por vez, sem misturar tudo.

O objetivo final é ter um serviço parecido com o que roda em produção de verdade:
registro de usuários, login com token, rotas protegidas, refresh de token,
controle de permissões e infraestrutura com banco de dados real.

**Esta tarefa cobre apenas a Fase 1.** As outras fases estão descritas abaixo só
pra você ter o mapa completo e entender onde essa primeira peça se encaixa. Não
implemente nada além da Fase 1.

---

## Overview das 5 fases (mapa geral)

| Fase | Objetivo | O que entra de novo |
|------|----------|---------------------|
| **1** | Registro e login | FastAPI, Pydantic, SQLAlchemy, SQLite, hashing de senha, geração de JWT |
| **2** | Rota protegida | Validação de JWT, dependência de autenticação, rota `/me` |
| **3** | Sessão robusta | Refresh tokens, expiração, logout |
| **4** | Autorização | Papéis/permissões (admin vs comum), testes automatizados |
| **5** | Produção | Migrations (Alembic), PostgreSQL, Docker |

> Ponto importante que costuma confundir: **o login (com senha) acontece uma vez
> e devolve um token. As chamadas seguintes usam só o token, nunca a senha de
> novo.** Na Fase 1 o token já é gerado no login, mas ainda não existe nenhuma
> rota que o exija — isso é de propósito. Quem vai "cobrar" o token é a Fase 2.

---

## História de usuário (modelo INVEST)

> **Como** uma pessoa que quer usar a aplicação,
> **eu quero** criar uma conta com email e senha e depois fazer login,
> **para que** eu receba um token que futuramente me dará acesso às áreas
> protegidas do sistema.

### Por que essa história é INVEST

- **I — Independent (Independente):** não depende de nenhuma outra fase para ser
  entregue e testada. É o ponto de partida.
- **N — Negotiable (Negociável):** os detalhes (nomes de campos, formato de
  resposta) podem ser ajustados na revisão; o valor central é registro + login.
- **V — Valuable (Valiosa):** entrega valor real — sem registro e login, nenhuma
  das outras fases existe.
- **E — Estimable (Estimável):** escopo fechado e claro, dá pra estimar (1–2 dias).
- **S — Small (Pequena):** cabe num único ciclo de trabalho, sem quebrar em mais partes.
- **T — Testable (Testável):** dá pra verificar objetivamente (ver critérios de
  aceitação abaixo).

---

## Escopo da Fase 1

### Dentro do escopo ✅

- Endpoint `POST /register` que cria um usuário (email + senha).
- Endpoint `POST /login` que valida as credenciais e retorna um token JWT.
- Senha armazenada **com hash** (nunca em texto puro).
- Persistência em **SQLite** via SQLAlchemy.
- Validação de entrada com Pydantic (email válido, senha mínima).

### Fora do escopo ❌ (não faça agora)

- Rotas protegidas que exigem token (isso é Fase 2).
- Refresh token, logout, expiração avançada (Fase 3).
- Papéis e permissões (Fase 4).
- Alembic, PostgreSQL, Docker (Fase 5).
- Front-end de qualquer tipo.

---

## Pré-requisitos

Antes de começar, garanta que você tem:

1. **Python 3.10 ou superior** instalado. Confirme com:
   ```bash
   python3 --version
   ```
2. Saber criar e ativar um **ambiente virtual** (`venv`).
3. Um editor de código (recomendo VScode) e um cliente HTTP para testar (a própria doc interativa do
   FastAPI em `/docs` já serve, ou use `curl`/Postman/Insomnia).

### Dependências que o projeto vai usar

Instale dentro do ambiente virtual:

```bash
pip install fastapi "uvicorn[standard]" sqlalchemy "pydantic[email]" "passlib[bcrypt]" "python-jose[cryptography]"
```

| Pacote | Para quê serve |
|--------|----------------|
| `fastapi` | Framework web / API |
| `uvicorn` | Servidor que roda a aplicação |
| `sqlalchemy` | ORM para falar com o banco |
| `pydantic[email]` | Validação de dados (inclui validação de email) |
| `passlib[bcrypt]` | Hashing seguro de senha |
| `python-jose[cryptography]` | Geração e assinatura do token JWT |

---

## Estrutura de arquivos sugerida

```
auth-service/
├── app/
│   ├── __init__.py
│   ├── main.py          # cria a aplicação FastAPI e registra as rotas
│   ├── database.py      # configuração da conexão SQLite + sessão
│   ├── models.py        # modelo User (tabela do banco)
│   ├── schemas.py       # schemas Pydantic (entrada e saída)
│   ├── security.py      # hashing de senha e geração de JWT
│   └── routes/
│       ├── __init__.py
│       └── auth.py      # endpoints /register e /login
├── docs/
│   └── TAREFA-FASE-1.md # este documento
├── requirements.txt
└── README.md
```

> A estrutura pode ser diferente, mas mantenha responsabilidades separadas: banco,
> modelo, schema, segurança e rotas em arquivos diferentes. Isso vai facilitar
> muito as próximas fases.

---

## Especificação dos endpoints

### `POST /register`

Cria um novo usuário.

**Request body:**
```json
{
  "email": "maria@exemplo.com",
  "password": "senhaSegura123"
}
```

**Resposta esperada (201 Created):**
```json
{
  "id": 1,
  "email": "maria@exemplo.com"
}
```
> Nunca retorne a senha (nem o hash) na resposta.

**Erros esperados:**
- `400` ou `409` se o email já estiver cadastrado.
- `422` se o email for inválido ou a senha não atender ao mínimo (validação do Pydantic).

---

### `POST /login`

Valida credenciais e devolve o token.

**Request body:**
```json
{
  "email": "maria@exemplo.com",
  "password": "senhaSegura123"
}
```

**Resposta esperada (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "token_type": "bearer"
}
```

**Erros esperados:**
- `401 Unauthorized` se o email não existir ou a senha estiver errada.
  > Dica de segurança: use a **mesma** mensagem de erro para "email não existe" e
  > "senha errada" (ex.: "credenciais inválidas"). Não entregue de graça a
  > informação de qual dos dois falhou.

---

## Regras e boas práticas obrigatórias

1. **Nunca salve a senha em texto puro.** Sempre salve ela encriptada (hash) (bcrypt via passlib).
2. **Nunca retorne senha nem hash** em nenhuma resposta da API.
3. A **`SECRET_KEY`** do JWT não fica escrita no código de produção — nesta fase
   pode deixar uma constante em `security.py`, mas **deixe um comentário** dizendo
   que na Fase 5 isso vira variável de ambiente.
4. Separe responsabilidades por arquivo (não jogue tudo no `main.py`).
5. O arquivo `.db` do SQLite e a pasta do `venv` devem entrar no `.gitignore`.

---

## Critérios de aceitação (Definition of Done)

A tarefa só está pronta quando **todos** os itens abaixo forem verdadeiros:

- [ ] O projeto sobe sem erro com `uvicorn app.main:app --reload`.
- [ ] A documentação interativa abre em `http://localhost:8000/docs`.
- [ ] `POST /register` cria um usuário e retorna `201` com `id` e `email` (sem senha).
- [ ] Registrar o **mesmo email duas vezes** retorna erro (400/409), não cria duplicado.
- [ ] Enviar email inválido ou senha muito curta retorna `422`.
- [ ] No banco, a coluna de senha guarda um **hash**, não o texto digitado.
- [ ] `POST /login` com credenciais corretas retorna `200` com `access_token` e `token_type: "bearer"`.
- [ ] `POST /login` com senha errada ou email inexistente retorna `401` com mensagem genérica.
- [ ] O token retornado é um JWT válido (dá pra decodificar e ver o identificador do usuário).
- [ ] Existe um `README.md` explicando como instalar dependências e rodar o projeto.
- [ ] `requirements.txt` está preenchido (`pip freeze > requirements.txt`).
- [ ] `.gitignore` ignora `venv/` e o arquivo `*.db`.

---

## Como testar manualmente

1. Suba o servidor:
   ```bash
   uvicorn app.main:app --reload
   ```
2. Abra `http://localhost:8000/docs`.
3. Chame `POST /register` com um email e senha válidos → deve retornar `201`.
4. Chame `POST /login` com as mesmas credenciais → copie o `access_token`.
5. Cole o token em [jwt.io](https://jwt.io) e confirme que dá pra ler o conteúdo
   (o identificador do usuário deve estar lá).
6. Tente logar com a senha errada → deve retornar `401`.

---

## Entrega

- Faça o trabalho em uma branch nova (ex.: `feature/fase-1-registro-login`).
- Não commite `venv/` nem o arquivo `.db`.
- Abra o PR referenciando esta tarefa e marque o Tech Lead para revisão.
- Na descrição do PR, cole um print ou o passo a passo do teste manual funcionando.

---

## Dúvidas?

Trava em qualquer ponto por mais de ~30 min? Chama. Perguntar cedo é sinal de
bom senso, não de fraqueza. Bom trabalho! 🚀
