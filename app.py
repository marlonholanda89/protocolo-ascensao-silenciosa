from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import random
import mercadopago
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersegredo")

# 🔥 NOVO (ANTI-QUEDA DE BANCO NO RENDER)
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

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


# 🔥 NOVO (NUNCA MAIS TELA BRANCA)
@app.errorhandler(500)
def erro_500(e):
    print("ERRO 500:", e)
    return render_template("erro.html"), 500

@app.errorhandler(404)
def erro_404(e):
    return "<h1>Página não encontrada</h1>", 404


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


acoes_produtivas = [
"Arrume sua cama agora.",
"Organize seu ambiente por 5 minutos.",
"Beba 500ml de água.",
"Lave o rosto e fique apresentável.",
"Fique 10 minutos sem celular e sem distração.",
"Corrija sua postura por 5 minutos.",
"Limpe algo ao seu redor (mesa, quarto, etc).",
"Respire fundo e se recomponha mentalmente.",
"Planeje rapidamente o resto do seu dia.",
"Saia para pegar ar por 2 minutos."
]

desafios_base = [
"Ler 10 páginas de um livro.",
"Treinar mesmo sem vontade.",
"Ficar 2 horas sem redes sociais.",
"Evitar açúcar hoje.",
"Beber pelo menos 2L de água.",
"Não reclamar de nada hoje.",
"Evitar conteúdo inútil.",
"Focar em melhorar sua postura o dia inteiro.",
"Não procrastinar nenhuma tarefa importante.",
"Finalizar algo que você vem adiando."
]

desafios_intermediario = [
"Ler 20 páginas.",
"Treinar com intensidade máxima.",
"3h sem redes sociais.",
"Banho gelado obrigatório.",
"Sem pornografia hoje.",
"Sem fast food.",
"Planejar amanhã antes de dormir.",
"Fazer algo desconfortável propositalmente.",
"Evitar dopamina barata o dia todo.",
"Acordar mais cedo que o normal."
]

desafios_elite = [
"Ler 30 páginas.",
"Treino pesado completo + disciplina total.",
"Sem redes sociais o dia inteiro.",
"Banho gelado + controle mental.",
"Dieta limpa 100% hoje.",
"Executar tudo sem reclamar.",
"1h de foco absoluto (deep work).",
"Zero distrações inúteis.",
"Treinar mesmo cansado.",
"Superar seu limite físico hoje."
]


frases = [
"A disciplina vence o talento.",
"Homens fortes fazem o que precisa ser feito.",
"Controle sua mente ou ela controla você.",
"Pequenas vitórias diárias criam grandes homens.",
"A dor de hoje é a força de amanhã.",
"Grandes homens são construídos em silêncio."
]


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


# 🔥 RANKING MELHORADO (SEM QUEBRAR)
@app.route("/ranking")
def ranking():

    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    try:
        usuarios = Usuario.query.order_by(Usuario.pontos.desc()).limit(100).all()

        posicao = None

        for i, u in enumerate(usuarios, start=1):
            if u.email == email:
                posicao = i
                break

        return render_template(
            "ranking.html",
            usuarios=usuarios,
            posicao=posicao,
            usuario_logado=email
        )

    except Exception as e:
        print("Erro ranking:", e)
        return "<h1>Erro ao carregar ranking</h1>"


@app.route("/conteudo")
def conteudo():
    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    usuario = Usuario.query.filter_by(email=email).first()

    if usuario.plano == "Gratis":
        return redirect(url_for("planos"))

    limites = {
        "Projeto Apex":30,
        "Código Ascensão":30,
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

    plano = usuario.plano.strip()
    conteudo = conteudos.get(plano, {}).get(numero)

    if conteudo is None:

    # 🔥 ESCALA DE TREINO INTELIGENTE
    if plano == "Projeto Apex":
        treino = f"""
{10 + numero*2} flexões
{15 + numero*2} agachamentos
{20 + numero*2}s prancha
+ caminhada leve 10 min
"""
        desafio = random.choice(desafios_base)

    elif plano == "Código Ascensão":
        treino = f"""
{20 + numero*3} flexões
{25 + numero*3} agachamentos
{30 + numero*2}s prancha
+ corrida leve 15 min
"""
        desafio = random.choice(desafios_intermediario)

    else:  # Protocolo Vértice
        treino = f"""
{30 + numero*4} flexões
{40 + numero*4} agachamentos
{45 + numero*3}s prancha
+ corrida ou cardio 20 min
+ exercício extra (abdominal ou barra)
"""
        desafio = random.choice(desafios_elite)

    conteudo = {
        "titulo": f"Dia {numero} - Evolução",
        "imagem": "vegeta1.jpeg",
        "treino": treino,
        "acao": random.choice(acoes_produtivas),
        "desafio": desafio,
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