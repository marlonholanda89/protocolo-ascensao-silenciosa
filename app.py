from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import random
import mercadopago
import os

app = Flask(__name__)
app.secret_key = "supersegredo"

ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
sdk = mercadopago.SDK(ACCESS_TOKEN)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///usuarios.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Usuario(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(100))

    email = db.Column(db.String(100), unique=True)

    senha = db.Column(db.String(100))

    plano = db.Column(db.String(50), default="Gratis")

    pontos = db.Column(db.Integer, default=0)

    streak = db.Column(db.Integer, default=0)


with app.app_context():
    db.create_all()


nome_plataforma = "Protocolo Ascensão Silenciosa"

dias_programa = 30


def calcular_nivel(pontos):

    niveis = [

        (350,"Ascendido"),
        (200,"Elite"),
        (120,"Guerreiro"),
        (50,"Discípulo"),
        (0,"Iniciado")

    ]

    for limite,nome in niveis:
        if pontos >= limite:
            return nome


# FRASES

frases = [

"A disciplina vence o talento.",

"Homens fortes fazem o que precisa ser feito.",

"Controle sua mente ou ela controla você.",

"Pequenas vitórias diárias criam grandes homens.",

"A dor de hoje é a força de amanhã.",

"Grandes homens são construídos em silêncio."

]


# DESAFIOS

desafios = [

"Banho gelado hoje.",

"Fique 2 horas sem redes sociais.",

"Faça 10 minutos de leitura.",

"Fique 1 hora sem celular.",

"Sem açúcar hoje.",

"Acorde 30 minutos mais cedo."

]


# AÇÕES RÁPIDAS

acoes = [

"Lave o rosto com água gelada.",

"Beba um copo grande de água.",

"Respire profundamente por 1 minuto.",

"Coloque gelo no rosto por 20 segundos.",

"Molhe o rosto com água fria."

]


# ALONGAMENTO

alongamentos = [

"Alongue pernas por 30 segundos.",

"Alongue braços por 30 segundos.",

"Alongue coluna por 30 segundos.",

"Respire fundo e alongue o pescoço."

]


# TREINOS POR PLANO

treinos_planos = {

"Projeto Apex":

"""

10 flexões  
15 agachamentos  
20s prancha  
Repetir 3x

""",


"Código Ascensão":

"""

20 flexões  
25 agachamentos  
30s prancha  
15 abdominais  
Repetir 3x

""",


"Protocolo Vértice":

"""

30 flexões  
40 agachamentos  
40s prancha  
25 abdominais  
20 burpees  
Repetir 4x

"""

}


@app.route("/")
def index():
    return render_template("index.html", nome_plataforma=nome_plataforma)


@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        nome = request.form.get("nome")

        email = request.form.get("email")

        senha = request.form.get("senha")

        usuario_existente = Usuario.query.filter_by(email=email).first()

        if usuario_existente:
            return render_template("register.html", error="Email já cadastrado")

        novo_usuario = Usuario(nome=nome,email=email,senha=senha)

        db.session.add(novo_usuario)

        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")

        senha = request.form.get("senha")

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.senha == senha:

            session["email"] = usuario.email

            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Email ou senha incorretos")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    usuario = Usuario.query.filter_by(email=email).first()

    nivel = calcular_nivel(usuario.pontos)

    return render_template(

        "dashboard.html",

        nome=usuario.nome,

        plano=usuario.plano,

        pontos=usuario.pontos,

        streak=usuario.streak,

        nivel=nivel

    )


@app.route("/conteudo")
def conteudo():

    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    usuario = Usuario.query.filter_by(email=email).first()

    if usuario.plano == "Gratis":
        return redirect(url_for("planos"))

    limites = {

        "Projeto Apex":10,

        "Código Ascensão":20,

        "Protocolo Vértice":30

    }

    limite = limites.get(usuario.plano,0)

    progresso_usuario = usuario.streak

    dias = []

    for i in range(1, limite+1):

        if i <= progresso_usuario:
            status = "completo"

        elif i == progresso_usuario + 1:
            status = "liberado"

        else:
            status = "bloqueado"

        dias.append({

            "numero": i,

            "status": status

        })

    return render_template("conteudo.html", dias=dias)


@app.route("/dia/<int:numero>")
def dia(numero):

    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    usuario = Usuario.query.filter_by(email=email).first()

    progresso_usuario = usuario.streak

    if numero > progresso_usuario + 1:
        return redirect(url_for("conteudo"))

    treino = treinos_planos.get(usuario.plano)

    conteudo = {

    "titulo":"Treinamento do Dia",

    "imagem":"goku1.jpeg",

    "treino":treino,

    "acao": random.choice(acoes),

    "desafio": random.choice(desafios),

    "alongamento": random.choice(alongamentos),

    "frase": random.choice(frases)

    }

    return render_template("dia.html", numero=numero, conteudo=conteudo)


@app.route("/completar_dia")
def completar_dia():

    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    usuario = Usuario.query.filter_by(email=email).first()

    xp = random.randint(10,20)

    usuario.pontos += xp

    usuario.streak += 1

    db.session.commit()

    return redirect(url_for("dashboard"))


@app.route("/planos")
def planos():
    return render_template("planos.html")


@app.route("/logout")
def logout():
    session.pop("email",None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)