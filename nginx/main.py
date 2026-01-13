import uuid

import redis
import uvicorn
from fastapi import FastAPI, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()
r = redis.Redis(host="mi_redis", port=6379, db=0, decode_responses=True)

# HTML con CSS integrado (Bonito y moderno)
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Acceso Seguro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background: #0f172a; /* Azul muy oscuro */
            margin: 0;
            color: #f1f5f9;
        }
        .login-card {
            background: #1e293b; /* Gris azulado oscuro */
            padding: 2.5rem;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            width: 100%;
            max-width: 350px;
            border: 1px solid #334155;
        }
        h2 {
            text-align: center;
            margin-bottom: 1.5rem;
            color: #38bdf8; /* Azul brillante */
            font-weight: 600;
        }
        .input-group { margin-bottom: 1rem; }
        label { display: block; margin-bottom: 0.5rem; font-size: 0.9rem; color: #94a3b8; }
        input {
            width: 100%;
            padding: 12px;
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 6px;
            box-sizing: border-box;
            color: white;
            outline: none;
            transition: border 0.3s;
        }
        input:focus { border-color: #38bdf8; }
        button {
            width: 100%;
            padding: 12px;
            background: #0284c7;
            border: none;
            color: white;
            font-weight: bold;
            border-radius: 6px;
            cursor: pointer;
            margin-top: 1rem;
            transition: background 0.3s;
        }
        button:hover { background: #0369a1; }
        .error {
            color: #fb7185;
            text-align: center;
            margin-top: 1rem;
            font-size: 0.85rem;
            background: rgba(251, 113, 133, 0.1);
            padding: 8px;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>Bienvenido</h2>
        <form action="/login" method="post">
            <div class="input-group">
                <label>Usuario</label>
                <input type="text" name="username" placeholder="Tu usuario" required autocomplete="off">
            </div>
            <div class="input-group">
                <label>Contraseña</label>
                <input type="password" name="password" placeholder="••••••••" required>
            </div>
            <button type="submit">Entrar al Sistema</button>
        </form>
    </div>
</body>
</html>
"""


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return LOGIN_HTML


@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    # Validamos contra Redis como antes
    stored_pw = r.get(username)
    if stored_pw and stored_pw == password:
        session_id = str(uuid.uuid4())
        # Guardamos la sesión en Redis (expira en 1 hora)
        r.setex(f"session:{session_id}", 3600, username)

        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response

    return HTMLResponse(
        content=LOGIN_HTML
        + "<p style='color:red; text-align:center'>Error de acceso</p>"
    )


@app.get("/verify")
async def verify(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        username = r.get(f"session:{session_id}")
        if username:
            return Response(headers={"X-User": username}, status_code=200)

    raise HTTPException(status_code=401)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
