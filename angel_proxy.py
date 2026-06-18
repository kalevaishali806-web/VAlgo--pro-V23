#!/usr/bin/env python3
"""
VAlgo Pro V23 — Angel One Proxy Server
Port: 5000
"""
import json, time, sys
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    import config
    CLIENT_ID   = config.CLIENT_ID
    API_KEY     = config.API_KEY
    TOTP_SECRET = config.TOTP_SECRET
    MPIN        = config.MPIN
except Exception as e:
    print(f"\n❌ config.py मध्ये missing: {e}")
    print("हे 4 variables असले पाहिजेत:")
    print("  CLIENT_ID, API_KEY, TOTP_SECRET, MPIN")
    sys.exit(1)

try:
    import pyotp
except ImportError:
    print("❌ pyotp नाही — चालवा: pip install pyotp")
    sys.exit(1)

try:
    from smartapi import SmartConnect
except ImportError:
    try:
        from SmartApi import SmartConnect
    except ImportError:
        print("❌ smartapi नाही — चालवा: pip install smartapi-python")
        sys.exit(1)

# ── Global token cache ─────────────────────────────────────
_cache = {"token": None, "ts": 0}

def get_totp():
    return pyotp.TOTP(TOTP_SECRET).now()

def login():
    global _cache
    # Reuse token if less than 6 hours old
    if _cache["token"] and (time.time() - _cache["ts"]) < 6*3600:
        return _cache["token"]
    print(f"\n⏳ Connecting... ({CLIENT_ID})")
    obj = SmartConnect(api_key=API_KEY)
    totp = get_totp()
    print(f"🔑 TOTP: {totp}  (5s मध्ये expire)")
    data = obj.generateSession(CLIENT_ID, MPIN, totp)
    if data.get("status"):
        jwt = data["data"]["jwtToken"]
        if jwt.lower().startswith("bearer "):
            jwt = jwt[7:].strip()
        _cache = {"token": jwt, "ts": time.time()}
        name = data["data"].get("name","")
        print(f"✅ Login successful!")
        print(f"   नाव  : {name}")
        return jwt
    else:
        print(f"❌ Login failed: {data.get('message','')}")
        return None

# ── HTTP Handler ───────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress default logs

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/token":
            jwt = login()
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            if jwt:
                resp = {"token": "Bearer " + jwt, "clientId": CLIENT_ID, "apiKey": API_KEY}
            else:
                resp = {"error": "Login failed"}
            self.wfile.write(json.dumps(resp).encode())

        elif self.path == "/balance":
            import urllib.request
            jwt = login()
            if not jwt:
                self.send_response(500); self.end_headers(); return
            req = urllib.request.Request(
                "https://apiconnect.angelone.in/rest/secure/angelbroking/user/v1/getRMS",
                headers={
                    "Authorization": "Bearer " + jwt,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-UserType": "USER",
                    "X-SourceID": "WEB",
                    "X-ClientLocalIP": "CLIENT_LOCAL_IP",
                    "X-ClientPublicIP": "CLIENT_PUBLIC_IP",
                    "X-MACAddress": "MAC_ADDRESS",
                    "X-PrivateKey": API_KEY
                }
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    data = r.read()
                self.send_response(200)
                self._cors()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                self.send_response(500); self.end_headers()

        elif self.path == "/rest/secure/angelbroking/user/v1/updateIPAddress":
            import urllib.request
            jwt = login()
            if not jwt:
                self.send_response(500); self.end_headers(); return
            req = urllib.request.Request(
                "https://apiconnect.angelone.in/rest/secure/angelbroking/user/v1/updateIPAddress",
                headers={"Authorization": "Bearer " + jwt, "Content-Type": "application/json", "Accept": "application/json", "X-UserType": "USER", "X-SourceID": "WEB", "X-ClientLocalIP": "CLIENT_LOCAL_IP", "X-ClientPublicIP": "CLIENT_PUBLIC_IP", "X-MACAddress": "MAC_ADDRESS", "X-PrivateKey": API_KEY}
            )
            try:
                res = urllib.request.urlopen(req)
                self.send_response(200); self._cors(); self.send_header("Content-Type","application/json"); self.end_headers()
                self.wfile.write(res.read())
            except Exception as e:
                self.send_response(500); self.end_headers()

        elif self.path == "/ping":
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')

        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        import urllib.request
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        jwt = login()
        if not jwt:
            self.send_response(500); self.end_headers(); return

        # Forward to Angel One
        url = "https://apiconnect.angelone.in" + self.path
        req = urllib.request.Request(url, data=body, headers={
            "Authorization": "Bearer " + jwt,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "CLIENT_LOCAL_IP",
            "X-ClientPublicIP": "CLIENT_PUBLIC_IP",
            "X-MACAddress": "MAC_ADDRESS",
            "X-PrivateKey": API_KEY
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read()
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(500)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

# ── Start Server ───────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("      VAlgo Pro V23 — Angel One Proxy Server")
    print("=" * 55)
    # Initial login test
    jwt = login()
    if not jwt:
        print("❌ Login failed — config.py check करा")
        sys.exit(1)
    print(f"\n🚀 Server चालू: http://127.0.0.1:5000")
    print("   VAlgo मध्ये Connect दाबा!")
    print("   थांबवायला: CTRL+C\n")
    server = HTTPServer(("127.0.0.1", 5000), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹ Server बंद")

@app.route('/ai-advice', methods=['POST', 'OPTIONS'])
def ai_advice():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST'
        return response
    import requests as req
    data = request.json
    res = req.post('https://api.anthropic.com/v1/messages',
        headers={
            'Content-Type': 'application/json',
            'x-api-key': 'इथे_key_paste_कर',
            'anthropic-version': '2023-06-01'
        },
        json=data,
        timeout=30
    )
    return jsonify(res.json())
