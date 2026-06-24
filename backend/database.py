import os
import json
from pathlib import Path
from datetime import datetime

DB_TYPE = "postgres" if os.environ.get("DATABASE_URL") else "sqlite"


class DBConnection:
    def __init__(self):
        self.conn = None
        self.db_type = DB_TYPE
        if DB_TYPE == "postgres":
            self._init_postgres()
        else:
            self._init_sqlite()

    def _init_postgres(self):
        import psycopg2
        import psycopg2.extras
        self.conn = psycopg2.connect(os.environ["DATABASE_URL"])
        self.conn.autocommit = False
        self._cursor_factory = psycopg2.extras.RealDictCursor

    def _init_sqlite(self):
        import sqlite3
        db_dir = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH") or Path(__file__).parent
        db_path = Path(db_dir) / "exploracolombia.db"
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA foreign_keys = ON")

    def execute(self, sql, params=None):
        if DB_TYPE == "postgres":
            pg_sql = sql.replace("?", "%s")
            cur = self.conn.cursor(cursor_factory=self._cursor_factory)
            cur.execute(pg_sql, params or ())
            is_insert = sql.strip().upper().startswith("INSERT") and " OR " not in sql.upper()[:12]
            if is_insert:
                try:
                    id_cur = self.conn.cursor()
                    id_cur.execute("SELECT LASTVAL()")
                    cur._lastrowid = id_cur.fetchone()[0]
                    id_cur.close()
                except Exception:
                    cur._lastrowid = None
            return cur
        else:
            return self.conn.execute(sql, params or ())

    def executescript(self, script):
        if DB_TYPE == "postgres":
            cur = self.conn.cursor()
            for statement in script.split(";"):
                s = statement.strip()
                if s:
                    cur.execute(s)
            cur.close()
        else:
            self.conn.executescript(script)

    def executemany(self, sql, params_seq):
        if DB_TYPE == "postgres":
            pg_sql = sql.replace("?", "%s")
            cur = self.conn.cursor()
            cur.executemany(pg_sql, params_seq)
            cur.close()
        else:
            self.conn.executemany(sql, params_seq)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


def get_db():
    return DBConnection()


def lastrowid(cur):
    if DB_TYPE == "postgres":
        return cur._lastrowid if hasattr(cur, "_lastrowid") else None
    return cur.lastrowid


def _schema_sqlite():
    return """
        CREATE TABLE IF NOT EXISTS destinos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            departamento TEXT NOT NULL,
            tipo TEXT NOT NULL,
            descripcion TEXT DEFAULT '',
            imagen TEXT DEFAULT '',
            imagenes TEXT DEFAULT '[]'
        );

        CREATE TABLE IF NOT EXISTS paquetes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            duracion TEXT DEFAULT '',
            precio INTEGER DEFAULT 0,
            cupo INTEGER DEFAULT 0,
            descripcion TEXT DEFAULT '',
            estado TEXT DEFAULT 'Disponible',
            imagen TEXT DEFAULT '',
            precio_oferta INTEGER,
            en_oferta INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS paquete_destinos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paquete_id INTEGER NOT NULL,
            destino_id INTEGER NOT NULL,
            FOREIGN KEY (paquete_id) REFERENCES paquetes(id),
            FOREIGN KEY (destino_id) REFERENCES destinos(id)
        );

        CREATE TABLE IF NOT EXISTS guias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT DEFAULT '',
            telefono TEXT DEFAULT '',
            estado TEXT DEFAULT 'Activo'
        );

        CREATE TABLE IF NOT EXISTS guia_idiomas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guia_id INTEGER NOT NULL,
            idioma TEXT NOT NULL,
            FOREIGN KEY (guia_id) REFERENCES guias(id)
        );

        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paquete_id INTEGER NOT NULL,
            destino_id INTEGER,
            guia_id INTEGER NOT NULL,
            fecha_salida TEXT DEFAULT '',
            estado TEXT DEFAULT 'Pendiente',
            total INTEGER DEFAULT 0,
            pagado INTEGER DEFAULT 0,
            cliente_nombre TEXT DEFAULT '',
            cliente_email TEXT DEFAULT '',
            cliente_telefono TEXT DEFAULT '',
            FOREIGN KEY (paquete_id) REFERENCES paquetes(id),
            FOREIGN KEY (destino_id) REFERENCES destinos(id),
            FOREIGN KEY (guia_id) REFERENCES guias(id)
        );

        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            verified INTEGER DEFAULT 0,
            verification_code TEXT,
            verification_expiry TEXT
        );

        CREATE TABLE IF NOT EXISTS _meta (key TEXT PRIMARY KEY, value TEXT);

        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reserva_id INTEGER NOT NULL,
            metodo TEXT NOT NULL,
            monto INTEGER NOT NULL,
            estado TEXT DEFAULT 'completado',
            referencia TEXT DEFAULT '',
            creada TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (reserva_id) REFERENCES reservas(id)
        );

        CREATE TABLE IF NOT EXISTS registros_pendientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            verification_code TEXT,
            verification_expiry TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS notificaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            relacion_id INTEGER DEFAULT NULL,
            leida INTEGER DEFAULT 0,
            creada TEXT NOT NULL
        );
    """


def _schema_postgres():
    return """
        CREATE TABLE IF NOT EXISTS destinos (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            departamento TEXT NOT NULL,
            tipo TEXT NOT NULL,
            descripcion TEXT DEFAULT '',
            imagen TEXT DEFAULT '',
            imagenes TEXT DEFAULT '[]'
        );

        CREATE TABLE IF NOT EXISTS paquetes (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            duracion TEXT DEFAULT '',
            precio INTEGER DEFAULT 0,
            cupo INTEGER DEFAULT 0,
            descripcion TEXT DEFAULT '',
            estado TEXT DEFAULT 'Disponible',
            imagen TEXT DEFAULT '',
            precio_oferta INTEGER,
            en_oferta INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS paquete_destinos (
            id SERIAL PRIMARY KEY,
            paquete_id INTEGER NOT NULL REFERENCES paquetes(id),
            destino_id INTEGER NOT NULL REFERENCES destinos(id)
        );

        CREATE TABLE IF NOT EXISTS guias (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            email TEXT DEFAULT '',
            telefono TEXT DEFAULT '',
            estado TEXT DEFAULT 'Activo'
        );

        CREATE TABLE IF NOT EXISTS guia_idiomas (
            id SERIAL PRIMARY KEY,
            guia_id INTEGER NOT NULL REFERENCES guias(id),
            idioma TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reservas (
            id SERIAL PRIMARY KEY,
            paquete_id INTEGER NOT NULL REFERENCES paquetes(id),
            destino_id INTEGER REFERENCES destinos(id),
            guia_id INTEGER NOT NULL REFERENCES guias(id),
            fecha_salida TEXT DEFAULT '',
            estado TEXT DEFAULT 'Pendiente',
            total INTEGER DEFAULT 0,
            pagado INTEGER DEFAULT 0,
            cliente_nombre TEXT DEFAULT '',
            cliente_email TEXT DEFAULT '',
            cliente_telefono TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            verified INTEGER DEFAULT 0,
            verification_code TEXT,
            verification_expiry TEXT
        );

        CREATE TABLE IF NOT EXISTS _meta (key TEXT PRIMARY KEY, value TEXT);

        CREATE TABLE IF NOT EXISTS pagos (
            id SERIAL PRIMARY KEY,
            reserva_id INTEGER NOT NULL REFERENCES reservas(id),
            metodo TEXT NOT NULL,
            monto INTEGER NOT NULL,
            estado TEXT DEFAULT 'completado',
            referencia TEXT DEFAULT '',
            creada TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS registros_pendientes (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            verification_code TEXT,
            verification_expiry TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS notificaciones (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            relacion_id INTEGER DEFAULT NULL,
            leida INTEGER DEFAULT 0,
            creada TIMESTAMP NOT NULL
        );
    """


def init_schema():
    conn = get_db()
    if DB_TYPE == "postgres":
        conn.executescript(_schema_postgres())
    else:
        conn.executescript(_schema_sqlite())
    conn.commit()
    conn.close()


def migrate():
    conn = get_db()
    try:
        conn.execute("ALTER TABLE destinos ADD COLUMN imagenes TEXT DEFAULT '[]'")
        print("Migracion: columna imagenes agregada a destinos")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE reservas ADD COLUMN destino_id INTEGER REFERENCES destinos(id)")
        print("Migracion: columna destino_id agregada a reservas")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE reservas ADD COLUMN cliente_nombre TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE reservas ADD COLUMN cliente_email TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE reservas ADD COLUMN cliente_telefono TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE paquetes ADD COLUMN precio_oferta INTEGER")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE paquetes ADD COLUMN en_oferta INTEGER DEFAULT 0")
    except Exception:
        pass
    conn.commit()
    conn.close()


def is_seeded():
    conn = get_db()
    row = conn.execute("SELECT value FROM _meta WHERE key = 'seeded'").fetchone()
    conn.close()
    return row is not None and row["value"] == "1"


def seed():
    conn = get_db()

    destinos = [
        ("Valle de Cocora", "Quindío", "Natural", "Hogar de la palma de cera, el árbol nacional. Un paraíso de niebla, verdes infinitos y naturaleza viva.", "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Valle_del_cocora_-_general_view.jpg/960px-Valle_del_cocora_-_general_view.jpg", '["https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Paisaje_Valle_del_Cocora.jpg/960px-Paisaje_Valle_del_Cocora.jpg","https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Valle_de_Cocora%2C_Colombia_02.jpg/960px-Valle_de_Cocora%2C_Colombia_02.jpg","https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/View_of_the_Cerro_Morrogacho_in_the_C%C3%B3cora_Valley.jpg/960px-View_of_the_Cerro_Morrogacho_in_the_C%C3%B3cora_Valley.jpg"]'),
        ("Ciudad Amurallada", "Cartagena", "Cultural", "Tesoro colonial bañado por el Caribe. Calles empedradas, balcones floridos y una historia que enamora.", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Centro_historico_de_Cartagena.jpg/960px-Centro_historico_de_Cartagena.jpg", '["https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Atardecer_en_Cartagena_de_Indias_desde_La_Popa..jpg/960px-Atardecer_en_Cartagena_de_Indias_desde_La_Popa..jpg","https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Ciudad_amurallada_fog.jpg/960px-Ciudad_amurallada_fog.jpg","https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/Clock_Tower_CTG_11_2019_1352.jpg/960px-Clock_Tower_CTG_11_2019_1352.jpg"]'),
        ("Minca", "Magdalena", "Aventura", "Capital ecológica de la Sierra Nevada. Cascadas, café de altura y avistamiento de aves.", "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/Amanecer_en_la_Sierra.jpg/960px-Amanecer_en_la_Sierra.jpg", '["https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/Amanecer_en_la_Cuchilla_-_Nevados_-_Santa_Marta_-_Flickr_-_Alejandro_Bayer.jpg/960px-Amanecer_en_la_Cuchilla_-_Nevados_-_Santa_Marta_-_Flickr_-_Alejandro_Bayer.jpg","https://upload.wikimedia.org/wikipedia/commons/thumb/9/96/Cuchilla_de_San_Lorenzo%2C_Sierra_Nevada_de_Santa_Marta%2C_Magdalena%2C_Colombia.jpg/960px-Cuchilla_de_San_Lorenzo%2C_Sierra_Nevada_de_Santa_Marta%2C_Magdalena%2C_Colombia.jpg","https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Quebrada_valencia_santa_marta.jpg/960px-Quebrada_valencia_santa_marta.jpg"]'),
        ("Parque Tayrona", "Magdalena", "Natural", "Joyas natural del Caribe colombiano. Playas de ensueño, selva virgen y ruinas Tayrona.", "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Arrecifes.jpg/960px-Arrecifes.jpg", '["https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Adventourscolombia-playa-cabo-san-juan-tayrona-national-park-colombia-01.jpg/960px-Adventourscolombia-playa-cabo-san-juan-tayrona-national-park-colombia-01.jpg","https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Adventourscolombia-tayrona-national-park-colombia.jpg/960px-Adventourscolombia-tayrona-national-park-colombia.jpg"]'),
        ("Caño Cristales", "Meta", "Natural", "El río más hermoso del mundo. Un espectáculo de colores creado por la naturaleza.", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Ca%C3%B1o_Cristales_01.jpg/960px-Ca%C3%B1o_Cristales_01.jpg", '["https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Ca%C3%B1o_Cristales2.JPG/960px-Ca%C3%B1o_Cristales2.JPG","https://upload.wikimedia.org/wikipedia/commons/thumb/a/ad/Ca%C3%B1o_cristales_%28La_Macarena%29.jpg/960px-Ca%C3%B1o_cristales_%28La_Macarena%29.jpg"]'),
        ("Guatapé", "Antioquia", "Cultural", "Pueblo colorido con el imponente Peñón de Guatapé.", "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/El_Pe%C3%B1ol_de_Guatap%C3%A9_%28The_Rock_of_Guatape%29_2017-04-10.jpg/960px-El_Pe%C3%B1ol_de_Guatap%C3%A9_%28The_Rock_of_Guatape%29_2017-04-10.jpg", '["https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Calle_de_Guatap%C3%A9.jpg/960px-Calle_de_Guatap%C3%A9.jpg","https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Guatap%C3%A9_25.jpg/960px-Guatap%C3%A9_25.jpg"]'),
        ("Desierto de la Tatacoa", "Huila", "Aventura", "Paisaje lunar de arcilla roja y gris. Perfecto para astroturismo.", "https://upload.wikimedia.org/wikipedia/commons/a/ac/Desierto_de_la_Tatacoa_-_camilogaleano%28com%29.jpg", '["https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/Desierto_de_la_Tatacoa%2C_Villavieja%2C_Huila%2C_Colombia._%282%29.JPG/960px-Desierto_de_la_Tatacoa%2C_Villavieja%2C_Huila%2C_Colombia._%282%29.JPG","https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Desierto_de_la_Tatacoa%2C_Villavieja%2C_Huila%2C_Colombia_%281%29.JPG/960px-Desierto_de_la_Tatacoa%2C_Villavieja%2C_Huila%2C_Colombia_%281%29.JPG","https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Desierto_de_la_Tatacoa_%28Huila%29%2C_Colombia.jpg/960px-Desierto_de_la_Tatacoa_%28Huila%29%2C_Colombia.jpg"]'),
        ("San Andrés", "San Andrés", "Natural", "Isla de aguas cristalinas de siete colores. Arena blanca y arrecifes.", "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Rocky_Cay_Beach.jpg/960px-Rocky_Cay_Beach.jpg", '["https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Playa_en_San_Andres.JPG/960px-Playa_en_San_Andres.JPG","https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Playa_Parque_Nacional_Natural_Archipi%C3%A9lago_de_San_Andr%C3%A9s.jpg/960px-Playa_Parque_Nacional_Natural_Archipi%C3%A9lago_de_San_Andr%C3%A9s.jpg","https://upload.wikimedia.org/wikipedia/commons/7/72/San_Andr%C3%A9s_Island_Colombia.JPG"]'),
    ]
    conn.executemany(
        "INSERT INTO destinos (nombre, departamento, tipo, descripcion, imagen, imagenes) VALUES (?, ?, ?, ?, ?, ?)",
        destinos,
    )

    paquetes = [
        ("Aventura Cafetera", "5 días", 1200000, 20, "Recorre el Eje Cafetero: Cocora, termales, fincas cafeteras y pueblos patrimoniales.", "Disponible", "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Bogota%27s_best_coffee._IMG_5865._png.jpg/960px-Bogota%27s_best_coffee._IMG_5865._png.jpg", 980000, 1),
        ("Caribe Mágico", "4 días", 980000, 15, "Sol, playa y cultura en Cartagena y el Parque Tayrona.", "Disponible", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Centro_historico_de_Cartagena.jpg/960px-Centro_historico_de_Cartagena.jpg", None, 0),
        ("Exploración Sierra Nevada", "6 días", 1500000, 12, "Aventura en Minca, Ciudad Perdida y la Sierra Nevada.", "Disponible", "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/Amanecer_en_la_Sierra.jpg/960px-Amanecer_en_la_Sierra.jpg", 1200000, 1),
        ("Río de Colores", "3 días", 850000, 18, "Visita a Caño Cristales en su temporada de colores.", "Disponible", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Ca%C3%B1o_Cristales_01.jpg/960px-Ca%C3%B1o_Cristales_01.jpg", None, 0),
        ("Aventura Total Colombia", "10 días", 3200000, 8, "El tour definitivo: Cocora, Cartagena, Tayrona, Caño Cristales y más.", "Disponible", "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Valle_del_cocora_-_general_view.jpg/960px-Valle_del_cocora_-_general_view.jpg", 2600000, 1),
        ("Isla Paraíso", "5 días", 2100000, 10, "San Andrés y Providencia: mar de siete colores y arrecifes.", "Disponible", "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Rocky_Cay_Beach.jpg/960px-Rocky_Cay_Beach.jpg", None, 0),
    ]
    conn.executemany(
        "INSERT INTO paquetes (nombre, duracion, precio, cupo, descripcion, estado, imagen, precio_oferta, en_oferta) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        paquetes,
    )

    pd_pairs = [(1, 1), (1, 6), (2, 2), (2, 4), (3, 3), (4, 5), (5, 1), (5, 2), (5, 4), (5, 5), (6, 8)]
    conn.executemany(
        "INSERT INTO paquete_destinos (paquete_id, destino_id) VALUES (?, ?)",
        pd_pairs,
    )

    guias_data = [
        ("Carlos Pérez", "carlos@exploracolombia.co", "+57 300 123 4567", "Activo", ["Español", "Inglés"]),
        ("Luisa Gómez", "luisa@exploracolombia.co", "+57 300 234 5678", "Activo", ["Español", "Francés"]),
        ("Andrés Martínez", "andres@exploracolombia.co", "+57 300 345 6789", "Activo", ["Español", "Inglés", "Portugués"]),
        ("María Torres", "maria@exploracolombia.co", "+57 300 456 7890", "Activo", ["Español", "Alemán"]),
        ("Jorge Ramírez", "jorge@exploracolombia.co", "+57 300 567 8901", "Activo", ["Español", "Inglés", "Italiano"]),
    ]
    for nombre, email, tel, estado, idiomas in guias_data:
        cur = conn.execute(
            "INSERT INTO guias (nombre, email, telefono, estado) VALUES (?, ?, ?, ?)",
            (nombre, email, tel, estado),
        )
        for idioma in idiomas:
            conn.execute(
                "INSERT INTO guia_idiomas (guia_id, idioma) VALUES (?, ?)",
                (lastrowid(cur), idioma),
            )

    reservas = [
        (1, 1, 1, "2026-06-15", "Confirmada", 1200000, 0, "Ana Rodríguez", "ana@email.com", "+57 310 111 2233"),
        (2, 2, 2, "2026-07-01", "Pendiente", 980000, 0, "Pedro López", "pedro@email.com", "+57 310 222 3344"),
        (3, 3, 3, "2026-05-28", "Confirmada", 1500000, 0, "Sofía Medina", "sofia@email.com", "+57 310 333 4455"),
        (4, 4, 1, "2026-08-10", "Confirmada", 850000, 0, "Luis Hernández", "luis@email.com", "+57 310 444 5566"),
        (5, 5, 5, "2026-09-05", "Pendiente", 3200000, 0, "Camila Vargas", "camila@email.com", "+57 310 555 6677"),
        (1, 6, 4, "2026-04-20", "Cancelada", 2100000, 0, "Ana Rodríguez", "ana@email.com", "+57 310 111 2233"),
    ]
    conn.executemany(
        "INSERT INTO reservas (paquete_id, destino_id, guia_id, fecha_salida, estado, total, pagado, cliente_nombre, cliente_email, cliente_telefono) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        reservas,
    )

    usuarios = [
        ("admin", "admin@exploracolombia.co", "admin", "Fox", "admin", 1, None, None),
        ("user", "user@exploracolombia.co", "user", "Usuario Demo", "user", 1, None, None),
    ]
    for username, email, password, nombre, role, verified, code, expiry in usuarios:
        existing = conn.execute(
            "SELECT id FROM usuarios WHERE username = ?", (username,)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO usuarios (username, email, password, nombre, role, verified, verification_code, verification_expiry) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (username, email, password, nombre, role, verified, code, expiry),
            )

    if DB_TYPE == "postgres":
        conn.execute("INSERT INTO _meta (key, value) VALUES ('seeded', '1') ON CONFLICT (key) DO NOTHING")
    else:
        conn.execute("INSERT OR IGNORE INTO _meta (key, value) VALUES ('seeded', '1')")

    conn.commit()
    conn.close()
    print("Base de datos poblada exitosamente!")
