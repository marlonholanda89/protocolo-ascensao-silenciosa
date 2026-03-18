from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import random
import mercadopago
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersegredo")

# TOKEN MERCADO PAGO
ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")

if ACCESS_TOKEN:
    sdk = mercadopago.SDK(ACCESS_TOKEN)
else:
    sdk = None

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    if "sslmode" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(BASE_DIR, "usuarios.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

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
    try:
        db.create_all()
    except Exception as e:
        print("Erro ao criar/verificar banco:", e)


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


acoes = [
"Coloque gelo no rosto por 20 segundos.",
"Lave o rosto com água gelada.",
"Beba um copo grande de água agora.",
"Respire profundamente por 1 minuto.",
"Molhe o rosto com água fria.",
"Fique 10 minutos sem celular.",
"Faça 30 segundos de respiração profunda.",
"Olhe para frente e respire fundo 20 vezes."
]


frases = [
"A disciplina vence o talento.",
"Homens fortes fazem o que precisa ser feito.",
"Controle sua mente ou ela controla você.",
"Pequenas vitórias diárias criam grandes homens.",
"A dor de hoje é a força de amanhã.",
"Grandes homens são construídos em silêncio."
]


# 🔥 NOVO: CONTEÚDO POR PLANO
conteudos = {

"Projeto Apex": {
1:{
"titulo":"Disciplina Inicial",
"imagem":"vegeta1.jpeg",
"treino":"10 flexões\n15 agachamentos\n20s prancha\nRepetir 3x",
"acao":"Lave o rosto com água gelada",
"desafio":"Leia 30 minutos hoje",
"frase":"Disciplina básica cria consistência."
}
},

"Código Ascensão": {
1:{
"titulo":"Controle Mental",
"imagem":"goku1.jpeg",
"treino":"20 flexões\n25 agachamentos\n30s prancha\nRepetir 3x",
"acao":"Gelo no rosto por 1 minuto",
"desafio":"1h sem celular + postura perfeita",
"frase":"Controle mental define quem vence."
}
},

"Protocolo Vértice": {
1:{
"titulo":"Modo Elite",
"imagem":"vegeta1.jpeg",
"treino":"30 flexões\n40 agachamentos\n45s prancha\nRepetir 4x",
"acao":"Gelo + respiração profunda",
"desafio":"Sem redes sociais + leitura + foco total",
"frase":"Você não é comum. Aja como elite."
}
}

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


@app.route("/ranking")
def ranking():
    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    usuarios = Usuario.query.order_by(
        Usuario.pontos.desc()
    ).limit(10).all()

    usuario = Usuario.query.filter_by(email=email).first()

    posicao = Usuario.query.filter(
        Usuario.pontos > usuario.pontos
    ).count() + 1

    return render_template(
        "ranking.html",
        usuarios=usuarios,
        posicao=posicao
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

    limite = 30 if usuario.plano == "Admin" else limites.get(usuario.plano, 0)

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

    if usuario.plano != "Admin" and numero > usuario.streak + 1:
        return redirect(url_for("conteudo"))

    # 🔥 NOVO: conteúdo por plano
    plano = usuario.plano
    conteudo = conteudos.get(plano, {}).get(numero)

    if conteudo is None:
        conteudo = {
        "titulo":"Treinamento de Ascensão",
        "imagem":"vegeta1.jpeg",
        "treino":"20 flexões\n30 agachamentos\n40 segundos prancha\nRepetir 3 vezes",
        "acao": random.choice(acoes),
        "desafio":"Banho gelado de 1 minuto hoje.",
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


# 🔥 ADMIN
@app.route("/admin")
def admin():

    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    usuario = Usuario.query.filter_by(email=email).first()

    if usuario.plano != "Admin":
        return redirect(url_for("dashboard"))

    usuarios = Usuario.query.all()

    precos = {
        "Projeto Apex": 10,
        "Código Ascensão": 49.90,
        "Protocolo Vértice": 99.90
    }

    faturamento = 0

    for u in usuarios:
        faturamento += precos.get(u.plano, 0)

    return render_template(
        "admin.html",
        usuarios=usuarios,
        faturamento=faturamento
    )


@app.route("/checkout/<plano>")
def checkout(plano):

    if not sdk:
        return "Erro: pagamento indisponível"

    precos = {
        "Projeto Apex": 10,
        "Código Ascensão": 49.90,
        "Protocolo Vértice": 99.90
    }

    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    usuario = Usuario.query.filter_by(email=email).first()

    preference_data = {
        "items": [
            {
                "title": plano,
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": precos[plano]
            }
        ],
        "payer": {
            "email": usuario.email
        },
        "notification_url": request.host_url + "webhook",
        "back_urls": {
            "success": request.host_url + "dashboard",
            "failure": request.host_url + "planos",
            "pending": request.host_url + "planos"
        },
        "auto_return": "approved"
    }

    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]

    return redirect(preference["init_point"])


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    if data and data.get("type") == "payment":

        payment_id = data["data"]["id"]

        payment_info = sdk.payment().get(payment_id)
        payment = payment_info["response"]

        if payment["status"] == "approved":

            email = payment["payer"]["email"]
            plano = payment["additional_info"]["items"][0]["title"]

            usuario = Usuario.query.filter_by(email=email).first()

            if usuario:
                usuario.plano = plano
                db.session.commit()

    return "ok"


@app.route("/logout")
def logout():
    session.pop("email",None)
    return redirect(url_for("index"))