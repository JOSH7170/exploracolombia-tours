import os
import sys
import random
import json
import smtplib
import socket
import subprocess
import threading
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime, timedelta

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from database import get_db, init_schema, migrate, is_seeded, seed, lastrowid

app = Flask(__name__, static_folder=None)
CORS(app)

# ─── EMAIL CONFIG ───
MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "").strip()
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "").strip()
MAIL_FROM = os.environ.get("MAIL_FROM", MAIL_USERNAME or "onboarding@resend.dev")

_has_api = bool(os.environ.get("RESEND_API_KEY", "").strip())
print(f"[DEBUG] API key presente al inicio: {_has_api}")
print(f"[DEBUG] MAIL_FROM: {MAIL_FROM}")


def _smtp_settings(email):
    domain = email.lower().split("@")[-1] if "@" in email else ""
    servers = {
        "gmail.com": ("smtp.gmail.com", 587),
        "outlook.com": ("smtp-mail.outlook.com", 587),
        "hotmail.com": ("smtp-mail.outlook.com", 587),
        "live.com": ("smtp-mail.outlook.com", 587),
        "hotmail.es": ("smtp-mail.outlook.com", 587),
        "yahoo.com": ("smtp.mail.yahoo.com", 587),
        "yahoo.es": ("smtp.mail.yahoo.com", 587),
    }
    custom_server = os.environ.get("MAIL_SERVER", "").strip()
    custom_port = os.environ.get("MAIL_PORT", "").strip()
    if custom_server and custom_port:
        return custom_server, int(custom_port)
    if domain in servers:
        return servers[domain]
    print(f"[AVISO] Dominio '{domain}' no reconocido. Usando Gmail por defecto.")
    return ("smtp.gmail.com", 587)


def send_email(to, subject, html_body):
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if api_key:
        sender_email = os.environ.get("MAIL_FROM", "joshuasaltarin@hotmail.com")
        try:
            body = json.dumps({
                "sender": {"email": sender_email, "name": "ExploraColombia Tours"},
                "to": [{"email": to}],
                "subject": subject,
                "htmlContent": html_body,
            }).encode()
            req = urllib.request.Request(
                "https://api.brevo.com/v3/smtp/email",
                data=body,
                headers={
                    "api-key": api_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=15)
            print(f"Correo enviado a {to} vía Brevo (HTTP {resp.status})")
            resp.close()
            return True
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            print(f"Error HTTP {e.code} de Brevo para {to}: {detail}")
            return False
        except Exception as e:
            print(f"Error al enviar correo vía Brevo a {to}: {e}")
            return False

    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print(f"[AVISO] SMTP no configurado. No se pudo enviar correo a {to}")
        print(f"[AVISO] Para configurar, edita backend/.env con tu correo y contraseña de aplicación")
        print(f"[AVISO]   - Gmail: genera contraseña en https://myaccount.google.com/apppasswords")
        print(f"[AVISO]   - Outlook: usa tu contraseña normal o contraseña de aplicación")
        return False
    server, port = _smtp_settings(MAIL_USERNAME)
    msg = MIMEText(html_body, "html")
    msg["Subject"] = subject
    msg["From"] = MAIL_FROM
    msg["To"] = to
    print(f"Enviando correo a {to} vía {server}:{port}...")
    try:
        with smtplib.SMTP(server, port, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"Correo enviado a {to}")
        return True
    except smtplib.SMTPAuthenticationError:
        print(f"ERROR: Credenciales incorrectas para {MAIL_USERNAME}")
        print(f"  - Gmail: usa una Contraseña de Aplicación, NO tu contraseña normal")
        print(f"  - Genera una en: https://myaccount.google.com/apppasswords")
        return False
    except smtplib.SMTPException as e:
        print(f"Error SMTP al enviar a {to}: {e}")
        return False
    except Exception as e:
        print(f"Error al enviar correo a {to}: {e}")
        return False


@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

FRONTEND_PATH = Path(__file__).parent.parent
STATIC_PATH = Path(__file__).parent / "static"

STATIC_FOLDER = STATIC_PATH if STATIC_PATH.exists() and STATIC_PATH.is_dir() else FRONTEND_PATH

# Auto-seed on first run
try:
    init_schema()
    migrate()
    if not is_seeded():
        print("Primera ejecución: poblando base de datos...")
        seed()
except Exception as e:
    print(f"ERROR al inicializar BD: {e}")
    import traceback
    traceback.print_exc()


# ─── HEALTHCHECK ───


@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/debug-env")
def debug_env():
    return jsonify({
        "RESEND_API_KEY": bool(os.environ.get("RESEND_API_KEY", "").strip()),
        "MAIL_USERNAME": bool(MAIL_USERNAME),
        "MAIL_PASSWORD": bool(MAIL_PASSWORD),
        "MAIL_FROM": MAIL_FROM or None,
    })


# ─── HELPERS ───


def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    return [dict(r) for r in rows]


def paginate(query, params, page=1, per_page=100):
    conn = get_db()
    total = conn.execute(
        f"SELECT COUNT(*) as count FROM ({query})", params
    ).fetchone()["count"]
    offset = (page - 1) * per_page
    all_params = list(params) + [per_page, offset]
    rows = conn.execute(
        f"{query} LIMIT ? OFFSET ?", all_params
    ).fetchall()
    conn.close()
    return {"data": rows_to_list(rows), "total": total}


def error_response(msg, status=400):
    return jsonify({"error": msg}), status


def create_notification(tipo, mensaje, relacion_id=None):
    conn = get_db()
    admin = conn.execute(
        "SELECT id FROM usuarios WHERE username = 'admin'"
    ).fetchone()
    if admin:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO notificaciones (usuario_id, tipo, mensaje, relacion_id, creada) VALUES (?, ?, ?, ?, ?)",
            (admin["id"], tipo, mensaje, relacion_id, now),
        )
        conn.commit()
    conn.close()


# ─────── AUTH ───────


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    login_id = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not login_id or not password:
        return error_response("Usuario o correo y contraseña requeridos")
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM usuarios WHERE (username = ? OR email = ?) AND password = ?",
        (login_id, login_id, password),
    ).fetchone()
    conn.close()
    if not user:
        return error_response("Credenciales inválidas", 401)
    if not user["verified"]:
        return error_response("Cuenta no verificada. Revisa tu correo para el código de verificación.", 403)
    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "nombre": user["nombre"],
        "role": user["role"],
    })


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    nombre = data.get("nombre", "").strip()
    email = data.get("email", "").strip().lower()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not nombre or not email or not username or not password:
        return error_response("Todos los campos son requeridos")
    if len(password) < 4:
        return error_response("La contraseña debe tener al menos 4 caracteres")
    if "@" not in email or "." not in email:
        return error_response("Correo electrónico inválido")

    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM usuarios WHERE username = ? OR email = ?",
        (username, email),
    ).fetchone()
    if existing:
        conn.close()
        return error_response("El usuario o correo ya está registrado", 409)

    conn.execute(
        "DELETE FROM registros_pendientes WHERE email = ? OR username = ?",
        (email, username),
    )

    code = str(random.randint(100000, 999999))
    expiry = (datetime.now() + timedelta(minutes=15)).isoformat()

    conn.execute(
        "INSERT INTO registros_pendientes (username, email, password, nombre, role, verification_code, verification_expiry) VALUES (?, ?, ?, ?, 'user', ?, ?)",
        (username, email, password, nombre, code, expiry),
    )
    conn.commit()
    conn.close()

    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#f9f9fc;border-radius:16px;">
        <div style="text-align:center;margin-bottom:24px;">
            <div style="width:64px;height:64px;background:#00522c;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;">
                <svg viewBox="0 0 40 40" width="32" height="32" style="display:block">
                    <circle cx="20" cy="20" r="17" stroke="#92ecae" stroke-width="1.5" fill="none"/>
                    <polygon points="20,3 24,20 20,37 16,20" fill="#92ecae"/>
                    <polygon points="3,20 20,16 37,20 20,24" fill="#92ecae" opacity="0.35"/>
                    <circle cx="20" cy="20" r="2.2" fill="#00522c"/>
                </svg>
            </div>
            <h1 style="font-family:Montserrat,sans-serif;color:#00522c;font-size:24px;margin:0;">ExploraColombia Tours</h1>
        </div>
        <div style="background:#fff;border-radius:12px;padding:32px;box-shadow:0 8px 32px rgba(0,109,60,0.05);">
            <h2 style="font-family:Montserrat,sans-serif;color:#1a1c1e;font-size:18px;margin:0 0 8px;">Verificaci&oacute;n de cuenta</h2>
            <p style="color:#3f4941;font-size:14px;line-height:1.6;margin:0 0 20px;">Usa el siguiente c&oacute;digo para verificar tu cuenta. Expira en 15 minutos.</p>
            <div style="background:#f3f3f6;border-radius:12px;padding:20px;text-align:center;">
                <span style="font-family:monospace;font-size:36px;font-weight:800;letter-spacing:8px;color:#00522c;">{code}</span>
            </div>
            <p style="color:#6f7a70;font-size:12px;margin:20px 0 0;text-align:center;">Si no solicitaste este c&oacute;digo, ignora este mensaje.</p>
        </div>
        <p style="text-align:center;color:#6f7a70;font-size:11px;margin-top:24px;">&copy; 2026 ExploraColombia Tours &mdash; Todos los derechos reservados</p>
    </div>
    """
    threading.Thread(target=send_email, args=(email, "Tu código de verificación - ExploraColombia", html), daemon=True).start()
    print(f"\nCODIGO DE VERIFICACION para {email}: {code}\n")

    resp = {
        "message": "Registro exitoso. Revisa tu correo para el código de verificación.",
        "email": email,
    }
    return jsonify(resp), 201


@app.route("/api/verify-code", methods=["POST"])
def verify_code():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    code = data.get("code", "").strip()

    if not email or not code:
        return error_response("Correo y código requeridos")

    conn = get_db()
    pending = conn.execute(
        "SELECT * FROM registros_pendientes WHERE email = ? AND verification_code = ?",
        (email, code),
    ).fetchone()

    if not pending:
        conn.close()
        return error_response("Código inválido", 400)

    expiry = datetime.fromisoformat(pending["verification_expiry"])
    if datetime.now() > expiry:
        conn.execute("DELETE FROM registros_pendientes WHERE id = ?", (pending["id"],))
        conn.commit()
        conn.close()
        return error_response("El código ha expirado. Regístrate nuevamente.", 400)

    conflict = conn.execute(
        "SELECT id FROM usuarios WHERE username = ? OR email = ?",
        (pending["username"], pending["email"]),
    ).fetchone()
    if conflict:
        conn.execute("DELETE FROM registros_pendientes WHERE id = ?", (pending["id"],))
        conn.commit()
        conn.close()
        return error_response("El usuario o correo ya fue registrado por otro proceso", 409)

    conn.execute(
        "INSERT INTO usuarios (username, email, password, nombre, role, verified, verification_code, verification_expiry) VALUES (?, ?, ?, ?, ?, 1, NULL, NULL)",
        (pending["username"], pending["email"], pending["password"], pending["nombre"], pending["role"]),
    )
    conn.execute("DELETE FROM registros_pendientes WHERE id = ?", (pending["id"],))
    conn.commit()
    conn.close()

    print(f"Cuenta verificada: {email}")
    return jsonify({"message": "Cuenta verificada exitosamente. Ahora puedes iniciar sesión."})


@app.route("/api/resend-code", methods=["POST"])
def resend_code():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return error_response("Correo requerido")

    conn = get_db()
    pending = conn.execute(
        "SELECT * FROM registros_pendientes WHERE email = ?",
        (email,),
    ).fetchone()
    if not pending:
        conn.close()
        return error_response("No hay registro pendiente de verificación con ese correo", 404)

    code = str(random.randint(100000, 999999))
    expiry = (datetime.now() + timedelta(minutes=15)).isoformat()
    conn.execute(
        "UPDATE registros_pendientes SET verification_code = ?, verification_expiry = ? WHERE id = ?",
        (code, expiry, pending["id"]),
    )
    conn.commit()
    conn.close()

    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#f9f9fc;border-radius:16px;">
        <div style="text-align:center;margin-bottom:24px;">
            <div style="width:64px;height:64px;background:#00522c;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;">
                <svg viewBox="0 0 40 40" width="32" height="32" style="display:block">
                    <circle cx="20" cy="20" r="17" stroke="#92ecae" stroke-width="1.5" fill="none"/>
                    <polygon points="20,3 24,20 20,37 16,20" fill="#92ecae"/>
                    <polygon points="3,20 20,16 37,20 20,24" fill="#92ecae" opacity="0.35"/>
                    <circle cx="20" cy="20" r="2.2" fill="#00522c"/>
                </svg>
            </div>
            <h1 style="font-family:Montserrat,sans-serif;color:#00522c;font-size:24px;margin:0;">ExploraColombia Tours</h1>
        </div>
        <div style="background:#fff;border-radius:12px;padding:32px;box-shadow:0 8px 32px rgba(0,109,60,0.05);">
            <h2 style="font-family:Montserrat,sans-serif;color:#1a1c1e;font-size:18px;margin:0 0 8px;">Nuevo c&oacute;digo de verificaci&oacute;n</h2>
            <p style="color:#3f4941;font-size:14px;line-height:1.6;margin:0 0 20px;">Usa el nuevo c&oacute;digo para verificar tu cuenta. Expira en 15 minutos.</p>
            <div style="background:#f3f3f6;border-radius:12px;padding:20px;text-align:center;">
                <span style="font-family:monospace;font-size:36px;font-weight:800;letter-spacing:8px;color:#00522c;">{code}</span>
            </div>
            <p style="color:#6f7a70;font-size:12px;margin:20px 0 0;text-align:center;">Si no solicitaste este c&oacute;digo, ignora este mensaje.</p>
        </div>
        <p style="text-align:center;color:#6f7a70;font-size:11px;margin-top:24px;">&copy; 2026 ExploraColombia Tours &mdash; Todos los derechos reservados</p>
    </div>
    """
    threading.Thread(target=send_email, args=(email, "Nuevo código de verificación - ExploraColombia", html), daemon=True).start()
    print(f"Nuevo codigo para {email}: {code}")

    return jsonify({"message": "Código reenviado a tu correo."}), 200


# ─── STATIC FILES & SPA FALLBACK ───


@app.route("/")
def index():
    return send_from_directory(str(STATIC_FOLDER), "index.html")


@app.route("/<path:path>")
def static_or_spa(path):
    full_path = STATIC_FOLDER / path
    if full_path.exists() and full_path.is_file():
        return send_from_directory(str(STATIC_FOLDER), path)
    return send_from_directory(str(STATIC_FOLDER), "index.html")


# ─────── DESTINOS ───────


@app.route("/api/destinos", methods=["GET"])
def get_destinos():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)
    return jsonify(paginate("SELECT * FROM destinos ORDER BY id", [], page, per_page))


@app.route("/api/destinos/<int:id>", methods=["GET"])
def get_destino(id):
    conn = get_db()
    row = conn.execute("SELECT * FROM destinos WHERE id = ?", (id,)).fetchone()
    conn.close()
    if not row:
        return error_response("Destino no encontrado", 404)
    return jsonify(row_to_dict(row))


@app.route("/api/destinos", methods=["POST"])
def create_destino():
    data = request.get_json(silent=True) or {}
    nombre = data.get("nombre", "").strip()
    departamento = data.get("departamento", "").strip()
    tipo = data.get("tipo", "").strip()
    if not nombre or not departamento or not tipo:
        return error_response("Campos requeridos: nombre, departamento, tipo")
    descripcion = data.get("descripcion", "")
    imagen = data.get("imagen", "")
    imagenes = data.get("imagenes", "[]")
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO destinos (nombre, departamento, tipo, descripcion, imagen, imagenes) VALUES (?, ?, ?, ?, ?, ?)",
        (nombre, departamento, tipo, descripcion, imagen, imagenes),
    )
    row = conn.execute("SELECT * FROM destinos WHERE id = ?", (lastrowid(cur),)).fetchone()
    conn.commit()
    conn.close()
    return jsonify(row_to_dict(row)), 201


@app.route("/api/destinos/<int:id>", methods=["PUT"])
def update_destino(id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM destinos WHERE id = ?", (id,)).fetchone()
    if not existing:
        conn.close()
        return error_response("Destino no encontrado", 404)
    data = request.get_json(silent=True) or {}
    conn.execute(
        "UPDATE destinos SET nombre=?, departamento=?, tipo=?, descripcion=?, imagen=?, imagenes=? WHERE id=?",
        (
            data.get("nombre", existing["nombre"]),
            data.get("departamento", existing["departamento"]),
            data.get("tipo", existing["tipo"]),
            data.get("descripcion", existing["descripcion"]),
            data.get("imagen", existing["imagen"]),
            data.get("imagenes", existing["imagenes"] if existing["imagenes"] else "[]"),
            id,
        ),
    )
    row = conn.execute("SELECT * FROM destinos WHERE id = ?", (id,)).fetchone()
    conn.commit()
    conn.close()
    return jsonify(row_to_dict(row))


@app.route("/api/destinos/<int:id>", methods=["DELETE"])
def delete_destino(id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM destinos WHERE id = ?", (id,)).fetchone()
    if not existing:
        conn.close()
        return error_response("Destino no encontrado", 404)
    conn.execute("DELETE FROM paquete_destinos WHERE destino_id = ?", (id,))
    conn.execute("DELETE FROM destinos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Destino eliminado"})


# ─────── PAQUETES ───────


@app.route("/api/paquetes", methods=["GET"])
def get_paquetes():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)
    result = paginate("SELECT * FROM paquetes ORDER BY id", [], page, per_page)
    conn = get_db()
    for p in result["data"]:
        destinos = conn.execute(
            "SELECT destino_id FROM paquete_destinos WHERE paquete_id = ?", (p["id"],)
        ).fetchall()
        p["destinos"] = [d["destino_id"] for d in destinos]
    conn.close()
    return jsonify(result)


@app.route("/api/paquetes/<int:id>", methods=["GET"])
def get_paquete(id):
    conn = get_db()
    row = conn.execute("SELECT * FROM paquetes WHERE id = ?", (id,)).fetchone()
    if not row:
        conn.close()
        return error_response("Paquete no encontrado", 404)
    destinos = conn.execute(
        "SELECT destino_id FROM paquete_destinos WHERE paquete_id = ?", (id,)
    ).fetchall()
    conn.close()
    result = row_to_dict(row)
    result["destinos"] = [d["destino_id"] for d in destinos]
    return jsonify(result)


@app.route("/api/paquetes", methods=["POST"])
def create_paquete():
    data = request.get_json(silent=True) or {}
    nombre = data.get("nombre", "").strip()
    if not nombre:
        return error_response("El nombre es requerido")
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO paquetes (nombre, duracion, precio, cupo, descripcion, estado, imagen, precio_oferta, en_oferta) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            nombre,
            data.get("duracion", ""),
            data.get("precio", 0),
            data.get("cupo", 0),
            data.get("descripcion", ""),
            data.get("estado", "Disponible"),
            data.get("imagen", ""),
            data.get("precioOferta"),
            data.get("enOferta", 0),
        ),
    )
    paquete_id = lastrowid(cur)
    for did in data.get("destinos", []):
        conn.execute(
            "INSERT INTO paquete_destinos (paquete_id, destino_id) VALUES (?, ?)",
            (paquete_id, did),
        )
    row = conn.execute("SELECT * FROM paquetes WHERE id = ?", (paquete_id,)).fetchone()
    conn.commit()
    conn.close()
    create_notification("sistema", f"Nuevo paquete creado: {nombre}", paquete_id)
    result = row_to_dict(row)
    result["destinos"] = data.get("destinos", [])
    return jsonify(result), 201


@app.route("/api/paquetes/<int:id>", methods=["PUT"])
def update_paquete(id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM paquetes WHERE id = ?", (id,)).fetchone()
    if not existing:
        conn.close()
        return error_response("Paquete no encontrado", 404)
    data = request.get_json(silent=True) or {}
    conn.execute(
        "UPDATE paquetes SET nombre=?, duracion=?, precio=?, cupo=?, descripcion=?, estado=?, imagen=?, precio_oferta=?, en_oferta=? WHERE id=?",
        (
            data.get("nombre", existing["nombre"]),
            data.get("duracion", existing["duracion"]),
            data.get("precio", existing["precio"]),
            data.get("cupo", existing["cupo"]),
            data.get("descripcion", existing["descripcion"]),
            data.get("estado", existing["estado"]),
            data.get("imagen", existing["imagen"]),
            data.get("precioOferta", existing["precio_oferta"]),
            data.get("enOferta", existing["en_oferta"]),
            id,
        ),
    )
    if "destinos" in data:
        conn.execute("DELETE FROM paquete_destinos WHERE paquete_id = ?", (id,))
        for did in data["destinos"]:
            conn.execute(
                "INSERT INTO paquete_destinos (paquete_id, destino_id) VALUES (?, ?)",
                (id, did),
            )
    row = conn.execute("SELECT * FROM paquetes WHERE id = ?", (id,)).fetchone()
    destinos = conn.execute(
        "SELECT destino_id FROM paquete_destinos WHERE paquete_id = ?", (id,)
    ).fetchall()
    conn.commit()
    conn.close()
    result = row_to_dict(row)
    result["destinos"] = [d["destino_id"] for d in destinos]
    return jsonify(result)


@app.route("/api/paquetes/<int:id>", methods=["DELETE"])
def delete_paquete(id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM paquetes WHERE id = ?", (id,)).fetchone()
    if not existing:
        conn.close()
        return error_response("Paquete no encontrado", 404)
    conn.execute("DELETE FROM paquete_destinos WHERE paquete_id = ?", (id,))
    conn.execute("UPDATE reservas SET paquete_id = NULL WHERE paquete_id = ?", (id,))
    conn.execute("DELETE FROM paquetes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Paquete eliminado"})


# ─────── GUIAS ───────


@app.route("/api/guias", methods=["GET"])
def get_guias():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)
    result = paginate("SELECT * FROM guias ORDER BY id", [], page, per_page)
    conn = get_db()
    for g in result["data"]:
        idiomas = conn.execute(
            "SELECT idioma FROM guia_idiomas WHERE guia_id = ?", (g["id"],)
        ).fetchall()
        g["idiomas"] = [i["idioma"] for i in idiomas]
    conn.close()
    return jsonify(result)


@app.route("/api/guias/<int:id>", methods=["GET"])
def get_guia(id):
    conn = get_db()
    row = conn.execute("SELECT * FROM guias WHERE id = ?", (id,)).fetchone()
    if not row:
        conn.close()
        return error_response("Guía no encontrado", 404)
    idiomas = conn.execute(
        "SELECT idioma FROM guia_idiomas WHERE guia_id = ?", (id,)
    ).fetchall()
    conn.close()
    result = row_to_dict(row)
    result["idiomas"] = [i["idioma"] for i in idiomas]
    return jsonify(result)


@app.route("/api/guias", methods=["POST"])
def create_guia():
    data = request.get_json(silent=True) or {}
    nombre = data.get("nombre", "").strip()
    if not nombre:
        return error_response("El nombre es requerido")
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO guias (nombre, email, telefono, estado) VALUES (?, ?, ?, ?)",
        (
            nombre,
            data.get("email", ""),
            data.get("telefono", ""),
            data.get("estado", "Activo"),
        ),
    )
    guia_id = lastrowid(cur)
    for idioma in data.get("idiomas", []):
        conn.execute(
            "INSERT INTO guia_idiomas (guia_id, idioma) VALUES (?, ?)",
            (guia_id, idioma),
        )
    conn.commit()
    conn.close()
    return jsonify({
        "id": guia_id,
        "nombre": nombre,
        "email": data.get("email", ""),
        "telefono": data.get("telefono", ""),
        "estado": data.get("estado", "Activo"),
        "idiomas": data.get("idiomas", []),
    }), 201


@app.route("/api/guias/<int:id>", methods=["PUT"])
def update_guia(id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM guias WHERE id = ?", (id,)).fetchone()
    if not existing:
        conn.close()
        return error_response("Guía no encontrado", 404)
    data = request.get_json(silent=True) or {}
    conn.execute(
        "UPDATE guias SET nombre=?, email=?, telefono=?, estado=? WHERE id=?",
        (
            data.get("nombre", existing["nombre"]),
            data.get("email", existing["email"]),
            data.get("telefono", existing["telefono"]),
            data.get("estado", existing["estado"]),
            id,
        ),
    )
    if "idiomas" in data:
        conn.execute("DELETE FROM guia_idiomas WHERE guia_id = ?", (id,))
        for idioma in data["idiomas"]:
            conn.execute(
                "INSERT INTO guia_idiomas (guia_id, idioma) VALUES (?, ?)",
                (id, idioma),
            )
    updated = conn.execute("SELECT * FROM guias WHERE id = ?", (id,)).fetchone()
    idiomas = conn.execute(
        "SELECT idioma FROM guia_idiomas WHERE guia_id = ?", (id,)
    ).fetchall()
    conn.commit()
    conn.close()
    result = row_to_dict(updated)
    result["idiomas"] = [i["idioma"] for i in idiomas]
    return jsonify(result)


@app.route("/api/guias/<int:id>", methods=["DELETE"])
def delete_guia(id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM guias WHERE id = ?", (id,)).fetchone()
    if not existing:
        conn.close()
        return error_response("Guía no encontrado", 404)
    conn.execute("DELETE FROM guia_idiomas WHERE guia_id = ?", (id,))
    conn.execute("UPDATE reservas SET guia_id = NULL WHERE guia_id = ?", (id,))
    conn.execute("DELETE FROM guias WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Guía eliminado"})


# ─────── CLIENTES ───────


# ─────── RESERVAS ───────

RESERVAS_SELECT = """
    SELECT id, paquete_id AS paqueteId, destino_id AS destinoId,
           guia_id AS guiaId, fecha_salida AS fechaSalida,
           estado, total, pagado,
           cliente_nombre AS clienteNombre, cliente_email AS clienteEmail,
           cliente_telefono AS clienteTelefono FROM reservas
"""


@app.route("/api/reservas", methods=["GET"])
def get_reservas():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)
    return jsonify(paginate(RESERVAS_SELECT + " ORDER BY id", [], page, per_page))


@app.route("/api/reservas/<int:id>", methods=["GET"])
def get_reserva(id):
    conn = get_db()
    row = conn.execute(RESERVAS_SELECT + " WHERE id = ?", (id,)).fetchone()
    conn.close()
    if not row:
        return error_response("Reserva no encontrada", 404)
    return jsonify(row_to_dict(row))


@app.route("/api/reservas", methods=["POST"])
def create_reserva():
    data = request.get_json(silent=True) or {}
    paquete_id = data.get("paqueteId")
    guia_id = data.get("guiaId")
    fecha_salida = data.get("fechaSalida")
    cliente_nombre = data.get("clienteNombre", "").strip()
    cliente_email = data.get("clienteEmail", "").strip().lower()
    cliente_telefono = data.get("clienteTelefono", "").strip()

    if not paquete_id or not guia_id or not fecha_salida or not cliente_nombre or not cliente_email:
        return error_response("Campos requeridos: paqueteId, guiaId, fechaSalida, clienteNombre, clienteEmail")

    conn = get_db()
    paquete = conn.execute("SELECT * FROM paquetes WHERE id = ?", (paquete_id,)).fetchone()
    if not paquete:
        conn.close()
        return error_response("Paquete no encontrado", 404)

    reservadas = conn.execute(
        "SELECT COUNT(*) as count FROM reservas WHERE paquete_id = ? AND estado != 'Cancelada'",
        (paquete_id,),
    ).fetchone()["count"]
    if reservadas >= paquete["cupo"]:
        conn.close()
        return error_response("No hay cupo disponible para este paquete", 400)

    estado = data.get("estado", "Pendiente")
    total = data.get("total", paquete["precio"])
    pagado = data.get("pagado", 0)
    cliente_nombre = data.get("clienteNombre", "").strip()
    cliente_email = data.get("clienteEmail", "").strip().lower()
    cliente_telefono = data.get("clienteTelefono", "").strip()
    destino_id = data.get("destinoId")

    cur = conn.execute(
        "INSERT INTO reservas (paquete_id, destino_id, guia_id, fecha_salida, estado, total, pagado, cliente_nombre, cliente_email, cliente_telefono) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (paquete_id, destino_id, guia_id, fecha_salida, estado, total, pagado, cliente_nombre, cliente_email, cliente_telefono),
    )
    reserva_id = lastrowid(cur)
    row = conn.execute(RESERVAS_SELECT + " WHERE id = ?", (reserva_id,)).fetchone()
    conn.commit()
    conn.close()

    try:
        conn2 = get_db()
        pn = conn2.execute("SELECT nombre FROM paquetes WHERE id = ?", (paquete_id,)).fetchone()
        conn2.close()
        if pn:
            create_notification("reserva", f"Nueva reserva: {cliente_nombre} - {pn['nombre']} para el {fecha_salida}", reserva_id)
    except Exception:
        pass

    return jsonify(row_to_dict(row)), 201


@app.route("/api/reservas/<int:id>", methods=["PUT"])
def update_reserva(id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM reservas WHERE id = ?", (id,)).fetchone()
    if not existing:
        conn.close()
        return error_response("Reserva no encontrada", 404)
    data = request.get_json(silent=True) or {}
    nuevo_estado = data.get("estado", existing["estado"])
    nuevo_pagado = data.get("pagado", existing["pagado"])
    conn.execute(
        "UPDATE reservas SET paquete_id=?, destino_id=?, guia_id=?, fecha_salida=?, estado=?, total=?, pagado=?, cliente_nombre=?, cliente_email=?, cliente_telefono=? WHERE id=?",
        (
            data.get("paqueteId", existing["paquete_id"]),
            data.get("destinoId", existing["destino_id"]),
            data.get("guiaId", existing["guia_id"]),
            data.get("fechaSalida", existing["fecha_salida"]),
            nuevo_estado,
            data.get("total", existing["total"]),
            nuevo_pagado,
            data.get("clienteNombre", existing["cliente_nombre"]),
            data.get("clienteEmail", existing["cliente_email"]),
            data.get("clienteTelefono", existing["cliente_telefono"]),
            id,
        ),
    )
    row = conn.execute(RESERVAS_SELECT + " WHERE id = ?", (id,)).fetchone()
    conn.commit()
    conn.close()

    try:
        if nuevo_estado != existing["estado"]:
            if nuevo_estado == "Cancelada":
                create_notification("alerta", f"Reserva #{id} cancelada", id)
            else:
                create_notification("reserva", f"Reserva #{id} actualizada a {nuevo_estado}", id)
        if nuevo_pagado > existing["pagado"]:
            cnombre = existing["cliente_nombre"] or "Cliente"
            total = existing["total"]
            porcentaje = round((nuevo_pagado / total) * 100) if total > 0 else 0
            create_notification("pago", f"Pago recibido: {cnombre} - ${nuevo_pagado:,.0f} ({porcentaje}%)", id)
    except Exception:
        pass

    return jsonify(row_to_dict(row))


@app.route("/api/reservas/<int:id>", methods=["DELETE"])
def delete_reserva(id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM reservas WHERE id = ?", (id,)).fetchone()
    if not existing:
        conn.close()
        return error_response("Reserva no encontrada", 404)
    conn.execute("DELETE FROM reservas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Reserva eliminada"})


@app.route("/api/reservas/<int:id>/pagar", methods=["POST"])
def pagar_reserva(id):
    data = request.get_json(silent=True) or {}
    metodo = data.get("metodo", "").strip()
    monto = data.get("monto", 0)

    if not metodo or monto <= 0:
        return error_response("Metodo de pago y monto requeridos")

    conn = get_db()
    reserva = conn.execute("SELECT * FROM reservas WHERE id = ?", (id,)).fetchone()
    if not reserva:
        conn.close()
        return error_response("Reserva no encontrada", 404)

    nuevo_pagado = reserva["pagado"] + monto
    conn.execute(
        "UPDATE reservas SET pagado = ?, estado = CASE WHEN ? >= total THEN 'Confirmada' ELSE 'Pendiente' END WHERE id = ?",
        (nuevo_pagado, nuevo_pagado, id),
    )
    conn.execute(
        "INSERT INTO pagos (reserva_id, metodo, monto, estado, referencia) VALUES (?, ?, ?, 'completado', ?)",
        (id, metodo, monto, data.get("referencia", "")),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM reservas WHERE id = ?", (id,)).fetchone()
    conn.close()

    paquete = get_db()
    p = paquete.execute("SELECT nombre FROM paquetes WHERE id = ?", (row["paquete_id"],)).fetchone()
    paquete.close()

    nombre_cliente = row["cliente_nombre"]
    email_cliente = row["cliente_email"]
    total = row["total"]
    pct = round((nuevo_pagado / total) * 100) if total > 0 else 0

    create_notification("pago", f"Pago recibido: {nombre_cliente} - ${monto:,.0f}", id)

    if email_cliente:
        html = f"""
        <div style="font-family:Inter,sans-serif;max-width:520px;margin:0 auto;padding:32px;background:#f9f9fc;border-radius:16px;">
            <div style="text-align:center;margin-bottom:24px;">
                <div style="width:64px;height:64px;background:#00522c;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;">
                    <svg viewBox="0 0 40 40" width="32" height="32" style="display:block">
                        <circle cx="20" cy="20" r="17" stroke="#92ecae" stroke-width="1.5" fill="none"/>
                        <polygon points="20,3 24,20 20,37 16,20" fill="#92ecae"/>
                        <polygon points="3,20 20,16 37,20 20,24" fill="#92ecae" opacity="0.35"/>
                        <circle cx="20" cy="20" r="2.2" fill="#00522c"/>
                    </svg>
                </div>
                <h1 style="font-family:Montserrat,sans-serif;color:#00522c;font-size:22px;margin:0;">ExploraColombia Tours</h1>
            </div>
            <div style="background:#fff;border-radius:12px;padding:32px;box-shadow:0 8px 32px rgba(0,109,60,0.05);">
                <h2 style="font-family:Montserrat,sans-serif;color:#1a1c1e;font-size:18px;margin:0 0 16px;">Reserva confirmada</h2>
                <p style="color:#3f4941;font-size:14px;line-height:1.6;margin:0 0 16px;">Hola <strong>{nombre_cliente}</strong>, tu reserva ha sido confirmada.</p>
                <div style="background:#f3f3f6;border-radius:12px;padding:20px;margin-bottom:16px;">
                    <p style="margin:0 0 8px;"><strong>Paquete:</strong> {p['nombre'] if p else 'N/A'}</p>
                    <p style="margin:0 0 8px;"><strong>Fecha de salida:</strong> {row['fecha_salida']}</p>
                    <p style="margin:0 0 8px;"><strong>Total:</strong> ${total:,.0f}</p>
                    <p style="margin:0 0 8px;"><strong>Pagado:</strong> ${nuevo_pagado:,.0f} ({pct}%)</p>
                    <p style="margin:0;"><strong>Método de pago:</strong> {metodo}</p>
                </div>
                <p style="color:#6f7a70;font-size:13px;margin:0;">Gracias por elegir ExploraColombia Tours. Si tienes preguntas, responde a este correo.</p>
            </div>
            <p style="text-align:center;color:#6f7a70;font-size:11px;margin-top:24px;">&copy; 2026 ExploraColombia Tours &mdash; Todos los derechos reservados</p>
        </div>
        """
        threading.Thread(target=send_email, args=(email_cliente, "Reserva confirmada - ExploraColombia Tours", html), daemon=True).start()

    return jsonify({"message": "Pago procesado exitosamente", "pagado": nuevo_pagado, "estado": row["estado"]})


# ─────── STATS / REPORTES ───────


@app.route("/api/stats", methods=["GET"])
def get_stats():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    month_str = now.strftime("%Y-%m")

    conn = get_db()
    paquetes_activos = conn.execute(
        "SELECT COUNT(*) as count FROM paquetes WHERE estado = 'Disponible'"
    ).fetchone()["count"]
    reservas_hoy = conn.execute(
        "SELECT COUNT(*) as count FROM reservas WHERE fecha_salida = ?", (today_str,)
    ).fetchone()["count"]
    cupo_total = conn.execute(
        "SELECT COALESCE(SUM(cupo), 0) as total FROM paquetes"
    ).fetchone()["total"]
    ingresos_mes = conn.execute(
        "SELECT COALESCE(SUM(pagado), 0) as total FROM reservas WHERE fecha_salida LIKE ? AND estado != 'Cancelada'",
        (month_str + "%",),
    ).fetchone()["total"]
    conn.close()

    return jsonify({
        "paquetesActivos": paquetes_activos,
        "reservasHoy": reservas_hoy,
        "cupoTotal": cupo_total,
        "ingresosMes": ingresos_mes,
    })


@app.route("/api/reportes/ocupacion", methods=["GET"])
def get_ocupacion():
    conn = get_db()
    paquetes = conn.execute("SELECT * FROM paquetes").fetchall()
    data = []
    for p in paquetes:
        reservadas = conn.execute(
            "SELECT COUNT(*) as count FROM reservas WHERE paquete_id = ? AND estado != 'Cancelada'",
            (p["id"],),
        ).fetchone()["count"]
        porcentaje = min(round((reservadas / p["cupo"]) * 100), 100) if p["cupo"] > 0 else 0
        data.append({
            "nombre": p["nombre"],
            "cupo": p["cupo"],
            "reservadas": reservadas,
            "porcentaje": porcentaje,
        })
    conn.close()
    return jsonify({"data": data})


@app.route("/api/reportes/ingresos", methods=["GET"])
def get_ingresos():
    meses = request.args.get("meses", 6, type=int)
    now = datetime.now()
    conn = get_db()
    data = []
    for i in range(meses - 1, -1, -1):
        d = datetime(now.year, now.month, 1)
        if i > 0:
            m = d.month - i
            y = d.year
            while m <= 0:
                m += 12
                y -= 1
            d = datetime(y, m, 1)
        key = d.strftime("%Y-%m")
        label = d.strftime("%b/%y").lower()
        ingresos = conn.execute(
            "SELECT COALESCE(SUM(pagado), 0) as total FROM reservas WHERE fecha_salida LIKE ? AND estado != 'Cancelada'",
            (key + "%",),
        ).fetchone()["total"]
        data.append({"label": label, "ingresos": ingresos})
    conn.close()
    return jsonify({"data": data})


# ─────── NOTIFICACIONES ───────

@app.route("/api/notificaciones", methods=["GET"])
def get_notificaciones():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM notificaciones ORDER BY creada DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return jsonify({"data": rows_to_list(rows)})


@app.route("/api/notificaciones/<int:id>/leer", methods=["POST"])
def leer_notificacion(id):
    conn = get_db()
    conn.execute("UPDATE notificaciones SET leida = 1 WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/notificaciones/leer-todas", methods=["POST"])
def leer_todas():
    conn = get_db()
    conn.execute("UPDATE notificaciones SET leida = 1")
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/notificaciones/<int:id>", methods=["DELETE"])
def eliminar_notificacion(id):
    conn = get_db()
    conn.execute("DELETE FROM notificaciones WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ─────── PERFIL Y CONFIGURACION ───────

@app.route("/api/cambiar-contrasena", methods=["POST"])
def cambiar_contrasena():
    data = request.get_json(silent=True) or {}
    actual = data.get("actual", "").strip()
    nueva = data.get("nueva", "").strip()
    usuario = data.get("usuario", "").strip()
    if not actual or not nueva or not usuario:
        return error_response("Todos los campos son requeridos")
    if len(nueva) < 4:
        return error_response("La nueva contraseña debe tener al menos 4 caracteres")
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM usuarios WHERE (username = ? OR email = ?) AND password = ?",
        (usuario, usuario, actual),
    ).fetchone()
    if not user:
        conn.close()
        return error_response("Contraseña actual incorrecta", 401)
    conn.execute("UPDATE usuarios SET password = ? WHERE id = ?", (nueva, user["id"]))
    conn.commit()
    conn.close()
    return jsonify({"message": "Contraseña actualizada correctamente"})


@app.route("/api/actualizar-perfil", methods=["POST"])
def actualizar_perfil():
    data = request.get_json(silent=True) or {}
    usuario = data.get("usuario", "").strip()
    nombre = data.get("nombre", "").strip()
    email = data.get("email", "").strip().lower()
    if not usuario or not nombre or not email:
        return error_response("Nombre y email son requeridos")
    if "@" not in email or "." not in email:
        return error_response("Email inválido")
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM usuarios WHERE username = ? OR email = ?",
        (usuario, usuario),
    ).fetchone()
    if not user:
        conn.close()
        return error_response("Usuario no encontrado", 404)
    otro = conn.execute(
        "SELECT id FROM usuarios WHERE email = ? AND id != ?", (email, user["id"])
    ).fetchone()
    if otro:
        conn.close()
        return error_response("Ese email ya está en uso por otro usuario")
    conn.execute("UPDATE usuarios SET nombre = ?, email = ? WHERE id = ?", (nombre, email, user["id"]))
    conn.commit()
    conn.close()
    return jsonify({"message": "Perfil actualizado correctamente", "nombre": nombre, "email": email})


# ─────── START ───────

def free_port(port):
    """Kill any process listening on the given port."""
    try:
        output = subprocess.check_output(
            ["netstat", "-ano"], shell=True, text=True
        )
        for line in output.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                subprocess.run(["taskkill", "/F", "/PID", pid],
                               capture_output=True, shell=True)
                print(f"  Puerto {port} liberado (PID {pid})")
    except Exception:
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    free_port(port)
    print(f"ExploraColombia API corriendo en http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
