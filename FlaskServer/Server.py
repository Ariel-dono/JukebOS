#! /usr/bin/python
from flask import Flask, g, jsonify, request, redirect
from flask_cors import CORS
import csv
import rethinkdb as r
import os

RDB_HOST =  'localhost'
RDB_PORT = 28015
MUSIC_DB = 'MusicStorage'

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','mp3'])
UPLOAD_FOLDER = '../ServiceDispatcher/music/'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)

# conexion antes de reques
@app.before_request
def before_request():
    try:
        g.db_conn = r.connect(host=RDB_HOST, port=RDB_PORT, db=MUSIC_DB)
    except RqlDriverError:
        abort(503, "No se pudo realizar conexion")

#conexion despues
@app.teardown_request
def teardown_request(exception):
    try:
        g.db_conn.close()
    except AttributeError:
        pass

@app.route("/<username>/<songname>", methods = ["POST"])
def updateSong(username,songname):
    file = request.files['file']
    if not file:
        return jsonify(msg = "No attached file"), 401

    file.save(os.path.join(app.config['UPLOAD_FOLDER'], (songname + '.mp3')))
    r.db('MusicStorage').table("MusicPath").insert({'username':username,'songname': songname,'songpath':UPLOAD_FOLDER+''+songname+'.mp3'}).run(g.db_conn)
    print ("instetar cancion"+userame+""+songname)
    return jsonify(msg = "username:"+username+ ", songname: "+songname), 201

@app.route("/<username>", methods = ["GET"])
def getUserMusic(username):
    selection = list(r.table('MusicPath').filter({"username": username }).pluck("songname").run(g.db_conn))
    return jsonify(msg = selection), 201

app.run(port=5001)
