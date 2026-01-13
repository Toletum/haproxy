import logging
import uuid

import redis
import uvicorn
from fastapi import Cookie, FastAPI, Form, Header, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger("AUTH")

templates = Jinja2Templates(directory="/app/proxy-auth/templates")

app = FastAPI()

# Conexión a Redis
BACKEND=os.getenv("BACKEND")

r = redis.Redis(host=BACKEND, port=6379, decode_responses=True)


@app.get("/auth/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    x_host: str = Header(None),
    x_real_ip: str = Header(None),
    error: str = Query(None),
):
    logger.info(
        f"Login page requested from Host: {x_host or 'Unknown'} from {x_real_ip}"
    )

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "host": x_host, "x_real_ip": x_real_ip, "error": error},
    )


@app.post("/auth/login")
def login(
    x_host: str = Header(None),
    x_real_ip: str = Header(None),
    username: str = Form(...),
    password: str = Form(...),
):
    logger.info(
        f"Login attempt for user: '{username}' '{x_real_ip}' via Host: {x_host}"
    )

    # Buscamos la clave exacta que tienes en Redis: user:nombre
    stored_password = r.get(f"user:{username}")

    if stored_password and stored_password == password:
        session_id = str(uuid.uuid4())

        try:
            r.setex(f"session:{session_id}", 3600, username)
        except Exception as e:
            logger.error(f"REDIS ERROR | Could not save session: {str(e)}")
            raise HTTPException(status_code=500)

        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

        response.set_cookie(
            key="ions_proxy_id", value=session_id, httponly=True, path="/"
        )
        return response

    return RedirectResponse(
        url="/auth/login?error=1", status_code=status.HTTP_303_SEE_OTHER
    )


@app.get("/auth/verify")
def verify(
    x_host: str = Header(None),
    x_real_ip: str = Header(None),
    ions_proxy_id: str = Cookie(None),
):
    if not ions_proxy_id:
        logger.warning(
            f"UNAUTHORIZED | No Session Cookie | Host: {x_host} | IP: {x_real_ip}"
        )
        raise HTTPException(status_code=401)

    try:
        username = r.get(f"session:{ions_proxy_id}")
    except Exception as e:
        logger.error(f"REDIS ERROR | Could not fetch session: {str(e)}")
        raise HTTPException(status_code=500)

    if username:
        logger.info(
            f"Verification success: User '{username}' '{x_real_ip}' for Host: {x_host}"
        )
        return {"authenticated": True, "user": username}

    raise HTTPException(status_code=401)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000, access_log=False)
