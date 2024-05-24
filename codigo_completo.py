from flask import Flask, jsonify, request, make_response
from banco_dados import Autor, Postagem, app, db
import json
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps

#-------------------------------------------------------------------------------------------------------------------------------------------------#

def token_obrigatorio(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'Mensagem': 'Token não foi incluído'}, 401)
        try:
            resultado = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            autor = Autor.query.filter_by(id_autor=resultado['id_autor']).first()
        except:
            return jsonify({'Mensagem': 'Token é inválido'}, 401)
        return f(autor, *args, **kwargs)
    return decorated

#-------------------------------------------------------------------------------------------------------------------------------------------------#

@app.route('/login')
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('Login inválido', 401, {'WWW-Authenticate': 'Basic realm="Login obrigatório"'})
    usuario = Autor.query.filter_by(nome=auth.username).first()
    if not usuario:
        return make_response('Login inválido', 401, {'WWW-Authenticate': 'Basic realm="Login obrigatório"'})
    if auth.password == usuario.senha:
        token = jwt.encode({'id_autor': usuario.id_autor, 'exp': datetime.now(timezone.utc) + timedelta(minutes=5)}, app.config['SECRET_KEY'])
        return jsonify({'token': token})
    return make_response('Login inválido', 401, {'WWW-Authenticate': 'Basic realm="Login obrigatório"'})

#-------------------------------------------------------------------------------------------------------------------------------------------------#

@app.route('/')     #https://localhost:5000/postagem
@token_obrigatorio
def obter_postagens(autor):
    postagens = Postagem.query.all()
    lista_postagens = []
    for postagem in postagens:
        postagem_atual = {}
        postagem_atual['titulo'] = postagem.titulo
        postagem_atual['id_autor'] = postagem.id_autor
        lista_postagens.append(postagem_atual)
    return jsonify({'Postagens': lista_postagens})

@app.route('/postagem/<int:indice>', methods=['GET'])   #https://localhost:5000/postagem/1
@token_obrigatorio
def obter_postagem_indice(autor, id_postagem):
    postagem = Postagem.query.filter_by(id_postagem=id_postagem).first()
    postagem_atual = {}
    try:
        postagem_atual['titulo'] = postagem.titulo
    except:
        pass
    postagem_atual['id_autor'] = postagem.id_autor
    return jsonify({'Postagens': postagem_atual})

@app.route('/postagem', methods=['POST'])   #https://localhost:5000/postagem
@token_obrigatorio
def nova_postagem(autor): 
    nova_postagem = request.get_json()
    postagem = Postagem(
        titulo=nova_postagem['titulo'], id_autor=nova_postagem['id_autor'])
    db.session.add(postagem)
    db.session.commit()
    return jsonify({'Mensagem': 'Postagem criada com sucesso'})

@app.route('/postagem/<int:indice>', methods=['PUT'])   #https://localhost:5000/postagem/1
@token_obrigatorio
def alterar_postagem(autor, id_postagem):
    postagem_alterada = request.get_json()
    postagem = Postagem.query.filter_by(id_postagem=id_postagem).first()
    try:
        postagem.titulo = postagem_alterada['titulo']
    except:
        pass
    try:
        postagem.id_autor = postagem_alterada['id_autor']
    except:
        pass
    db.session.commit()
    return jsonify({'Mensagem': 'Postagem alterada com sucessso'})

@app.route('/postagem/<int:indice>', methods=['DELETE'])    #https://localhost:5000/postagem/1
@token_obrigatorio
def excluir_postagem(autor, id_postagem):
    postagem_existente = Postagem.query.filter_by(id_postagem=id_postagem)
    if not postagem_existente:
        return jsonify({'Mensagem': 'A postagem não foi encontrada'})
    db.session.delete(postagem_existente)
    db.session.commit()
    return jsonify({'Mensagem': 'Postagem excluída com sucesso!'})

#-------------------------------------------------------------------------------------------------------------------------------------------------#

@app.route('/autores')  #http://localhost:5000/autores
@token_obrigatorio
def obter_autores(autor):
    autores = Autor.query.all()
    lista_autores = []
    for autor in autores:
        autor_atual = {}
        autor_atual['id_autor'] = autor.id_autor
        autor_atual['nome'] = autor.nome
        autor_atual['email'] = autor.email
        lista_autores.append(autor_atual)
    return jsonify({'autores': lista_autores})

@app.route('/autores/<int:id_autor>', methods=['GET'])     #http://localhost:5000/autores/1
@token_obrigatorio
def obter_autor_indice(autor, id_autor):
    autor = Autor.query.filter_by(id_autor=id_autor).first()
    if not autor:
        return jsonify(f'Autor não encontrado')
    autor_atual = {}
    autor_atual['id_autor'] = autor.id_autor
    autor_atual['nome'] = autor.nome
    autor_atual['email'] = autor.email
    return jsonify({'autor':autor_atual})

@app.route('/autores', methods=['POST'])    #http://localhost:5000/autores
@token_obrigatorio
def novo_autor(autor):
    novo_autor = request.get_json()
    autor = Autor(nome=novo_autor['nome'], senha=novo_autor['senha'], email=novo_autor['email'])
    
    db.session.add(autor)
    db.session.commit()

    return jsonify({'Mensagem': 'Autor criado com sucesso'}, 200)

@app.route('/autores/<int:id_autor>', methods=['PUT'])      #http://localhost:5000/autores
@token_obrigatorio
def alterar_autor(autor, id_autor):
    alterar_autor = request.get_json()
    autor = Autor.query.filter_by(id_autor=id_autor).first()
    if not autor:
        return jsonify({'Mensagem': 'Este autor não foi encontrado'})
    try:
        autor.nome = alterar_autor['nome']
    except:
        pass
    try:
        autor.email = alterar_autor['email']
    except:
        pass
    try:
        autor.senha = alterar_autor['senha']
    except:
        pass
    db.session.commit()
    return jsonify({'Mensagem': 'Autor alterado com sucesso!'})

@app.route('/autores/<int:id_autor>', methods=['DELETE'])    #http://localhost:5000/autores
@token_obrigatorio
def excluir_autor(autor, id_autor):
    autor_existente = Autor.query.filter_by(id_autor=id_autor).first()
    if not autor_existente:
        return jsonify({'Mensagem': 'Este autor não foi encontrado'})
    db.session.delete(autor_existente)
    db.session.commit()

    return jsonify({'Mensagem': 'Autor excluído com sucesso!'})

#-------------------------------------------------------------------------------------------------------------------------------------------------#

app.run(port=5000, host='localhost', debug=True) 
