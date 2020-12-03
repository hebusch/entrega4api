from flask import Flask, json, request, redirect, url_for, Response, render_template
from pymongo import MongoClient, TEXT


app = Flask(__name__)
USER = 'grupo23'
PASS = 'grupo23'
DATABASE = 'grupo23'
URL = f'mongodb://{USER}:{PASS}@gray.ing.puc.cl/{DATABASE}?authSource=admin'
client = MongoClient(URL)
db = client['grupo23']
mensajes = db.mensajes
usuarios = db.usuarios



def user_exist(uid):
    user = list(usuarios.find({"uid": uid}, {"_id": 0}))
    if user == []:
        return False
    return True

def forbidde_filter(resultados, filtrados):
    for diccionario in filtrados:
        filter_id = diccionario["mid"]
        for i in range(0, len(resultados)):
            if not resultados[i]:
                continue
            if filter_id == resultados[i]["mid"]:
                resultados[i] = None
             
    result = []
    for value in resultados:
        if value != None:
            result.append(value)

    return result


###GET: /
@app.route('/')
def index():
    return 'grupo 23 + grupo 28'


# GET /users
@app.route('/users')
def get_users():
    users = list(usuarios.find({}, {"_id" : 0}))
    return json.jsonify(users)

@app.route("/messages")
def get_messages():
    uid1 = request.args.get("id1")
    uid2 = request.args.get("id2")
    if uid1 and uid2:
        user1 = list(usuarios.find({"uid": int(uid1)}, {"_id": 0}))
        user2 = list(usuarios.find({"uid": int(uid2)}, {"_id": 0}))
        if user1 == [] and user2 == []:
            return json.jsonify({'HTTP 404 Not Found' : "Neither {}, nor {} exist.".format(uid1, uid2)}), 404
        elif user1 == []:
            return json.jsonify({'HTTP 404 Not Found' : "Unexisting user with id : {}.".format(uid1)}), 404
        elif user2 == []:
            return json.jsonify({'HTTP 404 Not Found' : "Unexisting user with id : {}.".format(uid2)}), 404
        else:
            msgs1 = list(mensajes.find({"sender": int(uid1), "receptant": int(uid2)}, {"_id": 0}))
            msgs2 = list(mensajes.find({"sender": int(uid2), "receptant": int(uid1)}, {"_id": 0}))
            return json.jsonify(msgs1 + msgs2)

    elif uid1:
        return json.jsonify({'HTTP 400 Bad Request' : "Given (1) argument. Expecting (2)."}), 400
    elif uid2:
        return json.jsonify({'HTTP 400 Bad Request' : "Given (1) argument. Expecting (2)."}), 400
    else: 
        messages = list(mensajes.find({}, {"_id": 0}))
        return json.jsonify(messages)

#DELETE
@app.route("/message/<int:mid>", methods=['DELETE'])
def delete_user_message(mid):
    if list(mensajes.find({"mid": int(mid)}, {"_id": 0})) == []:
        return json.jsonify({'HTTP 404 Not Found' : "Unexisting message."}), 404
    else:
        mensajes.remove({"mid": int(mid)})
        return json.jsonify({'HTTP 200 OK' : "Message deletion succesful."}), 200

# GET: /users/send/<int:uid>
@app.route("/users/<int:uid>")
def get_user_message(uid):
    usuario = list(usuarios.find({"uid": uid}, {"_id": 0}))
    if usuario == []:
        return json.jsonify({'HTTP 404 Not Found' : "Unexisting user."}), 404
    else:
        mensaje = list(mensajes.find({"sender": uid}, {"_id": 0}))
        return json.jsonify(usuario + mensaje)
             

@app.route("/messages/<int:mid>")
def get_messages_id(mid):
    msg = list(mensajes.find({"mid" : mid}, {"_id": 0}))
    if msg == []:
        return json.jsonify({'Error Not Found' : "id not exist"}), 404
    else:
        return json.jsonify(msg)


#metodo get o post (?)
@app.route("/text-search")
def text_search():
    
    diccionario = request.json

    if not diccionario:
        results = list(mensajes.find({}, {"_id": 0}))
        return json.jsonify(results)

    filtered = ""

    desired = None
    required = None
    forbidden = None
    user_id = None
    

    if "required" in diccionario.keys():
        required = diccionario["required"]
        filtered += " ".join([f"\"{s}\"" for s in required])
    
    if "desired" in diccionario.keys():
        desired = diccionario["desired"]
        filtered += " " + " ".join([f"{s}" for s in desired])
    
    if "forbidden" in diccionario.keys():
        forbidden = diccionario["forbidden"]
        filtered += " " + " ".join([f"-{s}" for s in forbidden])
    
    if "userId" in diccionario.keys():
        user_id = diccionario["userId"]

    # verificamos si el usuario ingresado existe
    if user_id:
        if not user_exist(user_id):
            return json.jsonify({'Error Not Found' : "id not exist"}), 404
        
        if not desired and not required and not forbidden:
            results = mensajes.find({"sender": user_id}, {"_id": 0})
            return json.jsonify([msg for msg in results])
        
        elif not desired and not required:
            mensajes.drop_index('message_text')
            mensajes.create_index([('message', TEXT)], name='message_text', default_language='none')
            required =  " ".join([f"{s}" for s in forbidden])
            results = list(mensajes.find({"sender": user_id}, {"_id": 0}))
            filtrados = list(mensajes.find({"$text":{"$search": required, "$language": "none"}, "sender": user_id}, {"_id": 0}))
            mensajes.drop_index('message_text')
            mensajes.create_index([('message', TEXT)], name='message_text', default_language='english')
            filtrados_2 = list(mensajes.find({"$text":{"$search": required}}, {"_id": 0}))
            for dict1 in filtrados_2:
                if dict1 not in filtrados:
                    filtrados.append(dict1)
            return json.jsonify(forbidde_filter(results, filtrados))

        results =  mensajes.find({"$text":{"$search": filtered}, "sender" : user_id},{"_id": 0})
        return json.jsonify([msg for msg in results])

    else:
        if not desired and not required and not forbidden:
            results = list(mensajes.find({}, {"_id": 0}))
            return json.jsonify(results)
        
        elif not desired and not required:
            mensajes.drop_index('message_text')
            mensajes.create_index([('message', TEXT)], name='message_text', default_language='none')
            required =  " ".join([f"{s}" for s in forbidden])
            resultados = list(mensajes.find({}, {"_id": 0}))
            filtrados = list(mensajes.find({"$text":{"$search": required, "$language": "none"}}, {"_id": 0}))
            mensajes.drop_index('message_text')
            mensajes.create_index([('message', TEXT)], name='message_text', default_language='english')
            filtrados_2 = list(mensajes.find({"$text":{"$search": required}}, {"_id": 0}))
            for dict1 in filtrados_2:
                if dict1 not in filtrados:
                    filtrados.append(dict1)
            
            return json.jsonify(forbidde_filter(resultados, filtrados))

        results =  mensajes.find({"$text":{"$search": filtered}},{"_id": 0})
        return json.jsonify([msg for msg in results])

#POST
@app.route('/messages', methods = ['POST'])
def post_message():
    mensaje_request = request.json
    if 'sender' not in mensaje_request.keys():
        return json.jsonify({'HTTP 404': 'Sender no ingresado'}), 404
    if 'date' not in mensaje_request.keys():
        return json.jsonify({'HTTP 404': 'Date no ingresado'}), 404
    if 'message' not in mensaje_request.keys():
        return json.jsonify({'HTTP 404': 'Message no ingresado'}), 404
    if 'lat' not in mensaje_request.keys():
        return json.jsonify({'HTTP 404': 'Lat no ingresado'}), 404
    if 'long' not in mensaje_request.keys():
        return json.jsonify({'HTTP 404': 'Long no ingresado'}), 404
    if 'receptant' not in mensaje_request.keys():
        return json.jsonify({'HTTP 404': 'Receptant no ingresado'}), 404
    else:
        mid = get_last_msg_id(mensajes)
        mensaje_request['mid'] = mid
        mensajes.insert_one(mensaje_request)
        return json.jsonify({'HTTP 200: SUCCESS'}), 200

def get_last_msg_id(mensajes):
    lista_mensajes = list(mensajes.find({}, {"_id": 0}))
    mids = set()
    for mensaje in lista_mensajes:
        mids.add(mensaje['mid'])
    for number in range(1, len(lista_mensajes) + 1):
        if not(number in mids):
            return number
    return len(lista_mensajes) + 1

if __name__ == '__main__':
    app.run(debug=True)