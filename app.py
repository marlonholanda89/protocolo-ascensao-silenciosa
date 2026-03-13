from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import random
import mercadopago

app = Flask(__name__)
app.secret_key = "supersegredo"

# TOKEN DO MERCADO PAGO
sdk = mercadopago.SDK("APP_USR-381894924064611-031313-091ca1eb5675ebfd0160c563529eef4c-3265389760")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///usuarios.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    senha = db.Column(db.String(100))
    plano = db.Column(db.String(50))
    pontos = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()

nome_plataforma = "Protocolo Ascensão Silenciosa"
dias_programa = 30

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

conteudos = {

1:{
"titulo":"Disciplina Inicial",
"imagem":"vegeta1.jpeg",
"treino":"10 flexões\n15 agachamentos\n20 segundos prancha\nRepetir 3 vezes",
"acao":"Lave o rosto com água gelada agora.",
"desafio":"Fique 2 horas sem redes sociais.",
"frase":"Disciplina é fazer o que precisa ser feito mesmo quando você não quer."
},

2:{
"titulo":"Controle Mental",
"imagem":"goku1.jpeg",
"treino":"12 flexões\n20 agachamentos\n30 segundos prancha\nRepetir 3 vezes",
"acao":"Respire profundamente por 30 segundos.",
"desafio":"Gelo no rosto 1 min.",
"frase":"A mente controla o corpo. Domine sua mente."
},

3:{
"titulo":"Foco Absoluto",
"imagem":"goku1.jpeg",
"treino":"15 flexões\n25 agachamentos\n30 segundos prancha\nRepetir 3 vezes",
"acao":"Coloque gelo no rosto por 20 segundos.",
"desafio":"1 hora sem celular.",
"frase":"Homens comuns se distraem. Homens fortes se concentram."
},

4:{
"titulo":"Rotina de Guerra",
"imagem":"goku1.jpeg",
"treino":"20 flexões\n30 agachamentos\n40 segundos prancha\nRepetir 3 vezes",
"acao":"Beba um copo grande de água agora.",
"desafio":"Banho gelado de 5 minuto.",
"frase":"A disciplina diária constrói guerreiros."
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
        plano = request.form.get("plano")

        usuario_existente = Usuario.query.filter_by(email=email).first()

        if usuario_existente:
            return render_template("register.html", error="Email já cadastrado")

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha=senha,
            plano=plano,
            pontos=0,
            streak=0
        )

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

    return render_template(
        "dashboard.html",
        nome=usuario.nome,
        plano=usuario.plano,
        pontos=usuario.pontos,
        streak=usuario.streak
    )

@app.route("/ranking")
def ranking():

    usuarios = Usuario.query.order_by(Usuario.pontos.desc()).all()

    return render_template("ranking.html", usuarios=usuarios)

@app.route("/conteudo")
def conteudo():

    email = session.get("email")

    if not email:
        return redirect(url_for("login"))

    usuario = Usuario.query.filter_by(email=email).first()
    progresso_usuario = usuario.streak

    dias = []

    for i in range(1, dias_programa+1):

        if i <= progresso_usuario:
            status = "completo"
        elif i == progresso_usuario + 1:
            status = "liberado"
        else:
            status = "bloqueado"

        dias.append({
            "numero":i,
            "status":status
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

    conteudo = conteudos.get(numero)

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

    usuario.pontos += 10
    usuario.streak += 1

    db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/planos")
def planos():
    return render_template("planos.html")

# CHECKOUT MERCADO PAGO
@app.route("/checkout/<plano>")
def checkout(plano):

    precos = {
        "Projeto Apex": 10,
        "Código Ascensão": 49.90,
        "Protocolo Vértice": 99.90
    }

    preference_data = {
        "items": [
            {
                "title": plano,
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": precos[plano]
            }
        ],
        "back_urls": {
            "success": "http://127.0.0.1:5000/dashboard",
            "failure": "http://127.0.0.1:5000/planos",
            "pending": "http://127.0.0.1:5000/planos"
        },
        "auto_return": "approved"
    }

    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]

    return redirect(preference["init_point"])

@app.route("/logout")
def logout():
    session.pop("email",None)
    return redirect(url_for("index"))
@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    if data["type"] == "payment":

        payment_id = data["data"]["id"]

        payment_info = sdk.payment().get(payment_id)
        payment = payment_info["response"]

        if payment["status"] == "approved":

            plano = payment["additional_info"]["items"][0]["title"]

            # aqui você poderia buscar o usuário pelo email
            # mas vamos liberar para o usuário logado

            email = session.get("email")

            if email:
                usuario = Usuario.query.filter_by(email=email).first()

                if usuario:
                    usuario.plano = plano
                    db.session.commit()

    return "ok"
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)