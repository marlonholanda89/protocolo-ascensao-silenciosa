from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "supersegredo"

# Nome da plataforma
nome_plataforma = "Protocolo Ascensão Silenciosa"

# Usuários armazenados em memória
usuarios = {}

# Pontos e streaks
progresso = {}

# Conteúdo diário por plano
conteudos = {
    "Básico": [
        {"tipo":"Alongamento","descricao":"Alongamento para postura (5 min)"},
        {"tipo":"Facial","descricao":"Exercícios simples para maxilar (3 min)"}
    ],
    "Intermediário": [
        {"tipo":"Corpo","descricao":"Treino avançado em casa (15 min)"},
        {"tipo":"Rosto","descricao":"Exercícios faciais detalhados (10 min)"},
        {"tipo":"Mental","descricao":"Protocolo de disciplina mental (5 min)"}
    ],
    "Premium": [
        {"tipo":"Corpo","descricao":"Treino PROTOCOLO VÉRTICE (20 min)"},
        {"tipo":"Rosto","descricao":"Exercícios faciais premium (15 min)"},
        {"tipo":"Mental","descricao":"Disciplina mental + meditação (10 min)"},
        {"tipo":"Motivação","descricao":"Frase do dia: 'Disciplina silenciosa. Ascensão inevitável.'"},
        {"tipo":"Imagem","descricao":"Imagem de referência inspiracional"}
    ]
}

# Rota Home
@app.route("/")
def index():
    return render_template("index.html", nome_plataforma=nome_plataforma)

# Rota Registro
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")
        plano = request.form.get("plano")

        usuarios[email] = {
            "nome": nome,
            "senha": senha,
            "plano": plano
        }

        progresso[email] = {
            "pontos": 0,
            "streak": 0
        }

        return redirect(url_for("login"))

    return render_template("register.html", nome_plataforma=nome_plataforma)

# Rota Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        email = request.form.get("email")
        senha = request.form.get("senha")

        usuario = usuarios.get(email)

        if usuario and usuario["senha"] == senha:
            session["email"] = email
            return redirect(url_for("dashboard"))

        return "Email ou senha incorretos"

    return render_template("login.html", nome_plataforma=nome_plataforma)

# Dashboard
@app.route("/dashboard")
def dashboard():

    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    usuario = usuarios[email]

    pontos = progresso[email]["pontos"]
    streak = progresso[email]["streak"]
    plano = usuario["plano"]

    return render_template(
        "dashboard.html",
        nome=usuario["nome"],
        plano=plano,
        pontos=pontos,
        streak=streak,
        nome_plataforma=nome_plataforma
    )

# Conteúdo diário
@app.route("/conteudo")
def conteudo():

    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    usuario = usuarios[email]

    plano = usuario["plano"]

    conteudo_texto = conteudos.get(plano, [])

    return render_template(
        "conteudo.html",
        conteudo=conteudo_texto,
        plano=plano,
        nome_plataforma=nome_plataforma
    )

# Completar dia
@app.route("/completar_dia")
def completar_dia():

    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    progresso[email]["pontos"] += 10
    progresso[email]["streak"] += 1

    return redirect(url_for("dashboard"))

# Planos
@app.route("/planos")
def planos():
    return render_template("planos.html", nome_plataforma=nome_plataforma)

# Pagamento / upgrade
@app.route("/pagamento", methods=["GET", "POST"])
def pagamento():

    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    if request.method == "POST":

        novo_plano = request.form.get("plano")

        usuarios[email]["plano"] = novo_plano

        return redirect(url_for("dashboard"))

    return render_template("pagamento.html", nome_plataforma=nome_plataforma)

# Logout
@app.route("/logout")
def logout():
    session.pop("email", None)
    return redirect(url_for("index"))

# Rodar servidor
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)