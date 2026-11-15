import json
import hashlib
import hmac
import os
import struct
from urllib.parse import quote
import time
import bcrypt
import mysql.connector
import base64
import shutil
from pathlib import Path
from bottle import route, run, template, post, get, hook, request, response, static_file
import gzip
import secrets

def loadDatabaseSettings(pathjs):
	pathjs = Path(pathjs)
	sjson = False
	if pathjs.exists():
		with pathjs.open() as data:
			sjson = json.load(data)
	return sjson
	
"""
function loadDatabaseSettings(pathjs):
	string = file_get_contents(pathjs);
	json_a = json_decode(string, true);
	return json_a;

"""
def getToken():
	return secrets.token_urlsafe(32)

# El token se guarda como sha256: un volcado de la BD no entrega sesiones validas
def hashToken(t):
	return hashlib.sha256(str(t).encode()).hexdigest()

MAX_INTENTOS, BLOQUEO_S, TOKEN_TTL_MIN = 5, 900, 30
# ponytail: en memoria (un proceso, se pierde al reiniciar); bloquear por uname permite DoS dirigido, pasar a BD y/o IP+uname si importa
intentos = {}    # uname -> (fallos, bloqueado_hasta)
ultimoTotp = {}  # id_Usuario -> ultimo codigo TOTP aceptado (anti-replay)
HASH_FALSO = bcrypt.hashpw(b"x", bcrypt.gensalt()).decode()  # iguala el tiempo de respuesta si el usuario no existe

def bloqueado(u):
	f, h = intentos.get(u, (0, 0))
	if time.time() >= h:
		intentos.pop(u, None)
		return False
	return f >= MAX_INTENTOS

def fallo(u):
	intentos[u] = (intentos.get(u, (0, 0))[0] + 1, time.time() + BLOQUEO_S)

@hook('after_request')
def cabeceras():
	# A02: cabeceras de seguridad; no-store evita cachear tokens y archivos
	response.set_header('X-Content-Type-Options', 'nosniff')
	if not request.path.startswith('/src/'):  # el front estatico si puede cachearse
		response.set_header('Cache-Control', 'no-store')

# Front: pagina con el gif y el audio de src/ (static_file impide salir de la carpeta)
@get('/')
def Front():
	return static_file('index.html', root='src')

@get('/src/<archivo>')
def Estatico(archivo):
	return static_file(archivo, root='src')

EXT_PERMITIDAS = {"png", "jpg", "jpeg", "gif"}

def totp(secret, t=None):
	# RFC 6238: HMAC-SHA1, 30 s, 6 digitos
	h = hmac.new(base64.b32decode(secret), struct.pack(">Q", int((t or time.time()) // 30)), "sha1").digest()
	o = h[-1] & 15
	return f"{(struct.unpack('>I', h[o:o+4])[0] & 0x7fffffff) % 10**6:06d}"

def verifyTotp(secret, code):
	# acepta ventana de +-30 s por desfase de reloj
	now = time.time()
	return any(hmac.compare_digest(totp(secret, now + d), str(code)) for d in (-30, 0, 30))

"""
*/
# Registro
/*
 * Este Registro recibe un JSON con el siguiente formato
 * 
 * : 
 *		"uname": "XXX",
 *		"email": "XXX",
 * 		"password": "XXX"
 * 
 * */
"""
@post('/Registro')
def Registro():
	dbcnf = loadDatabaseSettings('db.json');
	db = mysql.connector.connect(
		host='localhost', port = dbcnf['port'],
		database = dbcnf['dbname'],
		user = dbcnf['user'],
		password = dbcnf['password']
	)
	####/ obtener el cuerpo de la peticion
	if not request.json:
		return {"R":-1}
	R = 'uname' in request.json and 'email' in request.json and 'password' in request.json
	# TODO checar si estan vacio los elementos del json
	if not R:
		return {"R":-1}
	# A07: politica minima de contrasena (bcrypt solo usa los primeros 72 bytes)
	if not 8 <= len(str(request.json["password"]).encode()) <= 72:
		db.close()
		return {"R":-3}
	# TODO validar correo en json
	# TODO Control de error de la DB
	R = False
	try:
		h = bcrypt.hashpw(str(request.json["password"]).encode(), bcrypt.gensalt()).decode()
		secret = base64.b32encode(os.urandom(20)).decode()
		with db.cursor() as cursor:
			cursor.execute('insert into Usuario values(null,%s,%s,%s,%s)', (request.json["uname"], request.json["email"], h, secret))
			R = cursor.lastrowid
			db.commit()
		db.close()
	except Exception as e:
		print(e)
		return {"R":-2}
	# totp_secret se entrega una sola vez para registrarlo en la app autenticadora
	uri = f'otpauth://totp/insecure-webapi:{quote(str(request.json["uname"]))}?secret={secret}&issuer=insecure-webapi'
	return {"R":0,"D":R,"totp_secret":secret,"otpauth":uri}

"""
/*
 * Este Registro recibe un JSON con el siguiente formato
 * 
 * : 
 *		"uname": "XXX",
 * 		"password": "XXX"
 * 
 * 
 * Debe retornar un Token 
 * */
"""

@post('/Login')
def Login():
	dbcnf = loadDatabaseSettings('db.json');
	db = mysql.connector.connect(
		host='localhost', port = dbcnf['port'],
		database = dbcnf['dbname'],
		user = dbcnf['user'],
		password = dbcnf['password']
	)
	###/ obtener el cuerpo de la peticion
	if not request.json:
		return {"R":-1}
	######/
	R = 'uname' in request.json  and 'password' in request.json and 'totp' in request.json
	# TODO checar si estan vacio los elementos del json
	if not R:
		return {"R":-1}
	# A07: bloqueo temporal tras varios intentos fallidos
	u = str(request.json["uname"])
	if bloqueado(u):
		db.close()
		return {"R":-6}

	# TODO validar correo en json
	# TODO Control de error de la DB
	R = False
	try:
		with db.cursor() as cursor:
			cursor.execute('Select id,password,totp_secret from  Usuario where uname = %s', (request.json["uname"],))
			R = cursor.fetchall()
	except Exception as e:
		print(e)
		db.close()
		return {"R":-2}


	# checkpw siempre se ejecuta (con hash falso si no existe el usuario): sin enumeracion por tiempo
	if not bcrypt.checkpw(str(request.json["password"]).encode(), (R[0][1] if R else HASH_FALSO).encode()) or not R:
		fallo(u)
		db.close()
		return {"R":-3}
	# A07: TOTP invalido o reutilizado (replay)
	if not verifyTotp(R[0][2], request.json["totp"]) or ultimoTotp.get(R[0][0]) == str(request.json["totp"]):
		fallo(u)
		db.close()
		return {"R":-5}
	ultimoTotp[R[0][0]] = str(request.json["totp"])
	intentos.pop(u, None)

	T = getToken();
	try:
		with db.cursor() as cursor:
			cursor.execute('Delete from AccesoToken where id_Usuario = %s', (R[0][0],))
			cursor.execute('insert into AccesoToken values(%s,%s,now())', (R[0][0], hashToken(T)))
			db.commit()
			db.close()
			return {"R":0,"D":T}
	except Exception as e:
		print(e)
		db.close()
		return {"R":-4}

"""
/*
 * Este subir imagen recibe un JSON con el siguiente formato
 * 
 * 
 * 		"token: "XXX"
 *		"name": "XXX",
 * 		"data": "XXX",
 * 		"ext": "PNG"
 * 
 * 
 * Debe retornar codigo de estado
 * */
"""
@post('/Imagen')
def Imagen():
	#Directorio
	tmp = Path('tmp')
	if not tmp.exists():
		tmp.mkdir()
	img = Path('img')
	if not img.exists():
		img.mkdir()
	
	###/ obtener el cuerpo de la peticion
	if not request.json:
		return {"R":-1}
	######/
	R = 'name' in request.json  and 'data' in request.json and 'ext' in request.json  and 'token' in request.json
	# TODO checar si estan vacio los elementos del json
	if not R:
		return {"R":-1}
	# A01 (path traversal): la extension forma parte de la ruta destino, solo lista blanca
	if str(request.json['ext']).lower() not in EXT_PERMITIDAS:
		return {"R":-5}

	dbcnf = loadDatabaseSettings('db.json');
	db = mysql.connector.connect(
		host='localhost', port = dbcnf['port'],
		database = dbcnf['dbname'],
		user = dbcnf['user'],
		password = dbcnf['password']
	)

	# Validar si el usuario esta en la base de datos
	TKN = request.json['token'];
	
	R = False
	try:
		with db.cursor() as cursor:
			cursor.execute('select id_Usuario from AccesoToken where token = %s and fecha > now() - interval %s minute', (hashToken(TKN), TOKEN_TTL_MIN))
			R = cursor.fetchall()
	except Exception as e: 
		print(e)
		db.close()
		return {"R":-2}
	
	
	# A01: sin token valido no se sube nada
	if not R:
		db.close()
		return {"R":-4}
	id_Usuario = R[0][0];
	with open(f'tmp/{id_Usuario}',"wb") as imagen:
		imagen.write(base64.b64decode(request.json['data'].encode()))
	
	############################
	############################
	# Guardar info del archivo en la base de datos
	try:
		with db.cursor() as cursor:
			cursor.execute('insert into Imagen values(null,%s,"img/",%s)', (request.json["name"], id_Usuario))
			cursor.execute('select max(id) as idImagen from Imagen where id_Usuario = %s', (id_Usuario,))
			R = cursor.fetchall()
			idImagen = R[0][0];
			cursor.execute('update Imagen set ruta = %s where id = %s', (f"img/{idImagen}.{request.json['ext']}", idImagen))
			db.commit()
			# Mover archivo a su nueva locacion
			shutil.move('tmp/'+str(id_Usuario),'img/'+str(idImagen)+'.'+str(request.json['ext']))
			return {"R":0,"D":idImagen}
	except Exception as e: 
		print(e)
		db.close()
		return {"R":-3}
	
"""
/*
 * Este Registro recibe un JSON con el siguiente formato
 * 
 * : 
 * 		"token: "XXX",
 * 		"id": "XXX"
 * 
 * 
 * Debe retornar un Token 
 * */
"""

@post('/Descargar')
def Descargar():
	dbcnf = loadDatabaseSettings('db.json');
	db = mysql.connector.connect(
		host='localhost', port = dbcnf['port'],
		database = dbcnf['dbname'],
		user = dbcnf['user'],
		password = dbcnf['password']
	)
	
	###/ obtener el cuerpo de la peticion
	if not request.json:
		return {"R":-1}
	######/
	R = 'token' in request.json and 'id' in request.json  
	# TODO checar si estan vacio los elementos del json
	if not R:
		return {"R":-1}
	
	# TODO validar correo en json
	# Comprobar que el usuario sea valido
	TKN = request.json['token'];
	# A05: id estricto; MySQL convertiria '1 or 1=1' en 1 por prefijo numerico
	try:
		idImagen = int(request.json['id'])
	except (ValueError, TypeError):
		db.close()
		return {"R":-1}
	
	R = False
	try:
		with db.cursor() as cursor:
			cursor.execute('select id_Usuario from AccesoToken where token = %s and fecha > now() - interval %s minute', (hashToken(TKN), TOKEN_TTL_MIN))
			R = cursor.fetchall()
	except Exception as e: 
		print(e)
		db.close()
		return {"R":-2}
	
	# A01: token obligatorio
	if not R:
		db.close()
		return {"R":-5}
	id_Usuario = R[0][0]
	# Buscar imagen y enviarla (A01/IDOR: solo si pertenece al usuario del token)

	try:
		with db.cursor() as cursor:
			cursor.execute('Select name,ruta from  Imagen where id = %s and id_Usuario = %s', (idImagen, id_Usuario))
			R = cursor.fetchall()
	except Exception as e: 
		print(e)
		db.close()
		return {"R":-3}
	db.close()
	if not R:
		return {"R":-4}
	# URL aleatoria de un solo uso, vigente 5 min
	u = secrets.token_urlsafe(32)
	enlaces[u] = (R[0][1], time.time() + 300)
	return {"R":0,"D":f"/Descargar/{u}"}

# ponytail: dict en memoria (un solo proceso, se pierde al reiniciar); tabla en BD si se necesita persistir
enlaces = {}

"""
/*
 * GET /Descargar/<url aleatoria>
 * Retorna el archivo comprimido con gzip y codificado en hex (text/plain)
 * */
"""
@get('/Descargar/<u>')
def DescargarArchivo(u):
	ruta, exp = enlaces.pop(u, (None, 0))
	if not ruta or exp < time.time():
		response.status = 404
		return {"R":-1}
	response.content_type = 'text/plain'
	return gzip.compress(Path(ruta).read_bytes()).hex()

if __name__ == '__main__':
    run(host='localhost', port=8080, debug=False)