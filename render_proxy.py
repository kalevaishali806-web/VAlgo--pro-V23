from flask import Flask, request, jsonify, make_response
import json, time, pyotp, os

app = Flask(__name__)

CLIENT_ID   = os.environ.get('CLIENT_ID','')
API_KEY     = os.environ.get('API_KEY','')
TOTP_SECRET = os.environ.get('TOTP_SECRET','')
MPIN        = os.environ.get('MPIN','')

_cache = {"token": None, "ts": 0}

def cors(r):
    r.headers['Access-Control-Allow-Origin']='*'
    r.headers['Access-Control-Allow-Headers']='*'
    r.headers['Access-Control-Allow-Methods']='GET,POST,OPTIONS'
    return r

def login():
    global _cache
    if _cache["token"] and (time.time()-_cache["ts"])<6*3600:
        return _cache["token"]
    from SmartApi import SmartConnect
    obj=SmartConnect(api_key=API_KEY)
    totp=pyotp.TOTP(TOTP_SECRET).now()
    data=obj.generateSession(CLIENT_ID,MPIN,totp)
    if data.get("status"):
        jwt=data["data"]["jwtToken"]
        if jwt.lower().startswith("bearer "): jwt=jwt[7:].strip()
        _cache={"token":jwt,"ts":time.time()}
        return jwt
    return None

@app.route('/ping')
def ping():
    return cors(make_response(jsonify({"status":"ok"})))

@app.route('/token')
def token():
    jwt=login()
    r=jsonify({"token":"Bearer "+jwt,"clientId":CLIENT_ID,"apiKey":API_KEY} if jwt else {"error":"Login failed"})
    return cors(make_response(r))

@app.route('/<path:path>', methods=['GET','POST','OPTIONS'])
def proxy(path):
    if request.method=='OPTIONS':
        return cors(make_response('',200))
    import urllib.request
    jwt=login()
    if not jwt: return cors(make_response
ñ
