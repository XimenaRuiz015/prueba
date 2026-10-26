from sqlalchemy.orm import Session
from app.database.models import Proyecto, Multimedia, PublicacionBlog, Usuario, CodigoRecuperacion

def crear_proyecto(db: Session, datos: dict) -> Proyecto:
    proyecto = Proyecto(
        titulo=datos.get("titulo"),
        cliente=datos.get("cliente"),
        ubicacion=datos.get("ubicacion"),
        categoria=datos.get("categoria", "General"),
        estado=datos.get("estado", "En ejecución"),
        maquinaria=datos.get("maquinaria"),
        descripcion=datos.get("descripcion"),
        imagen_url=datos.get("imagen_url"),
        creado_por=datos.get("creado_por", "Freddy")
    )
    db.add(proyecto)
    db.commit()
    db.refresh(proyecto)
    return proyecto

def obtener_proyectos(db: Session, skip: int = 0, limit: int = 200):
    return db.query(Proyecto).order_by(Proyecto.creado_en.desc()).offset(skip).limit(limit).all()

def obtener_proyecto_por_id(db: Session, proyecto_id: int):
    return db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()

import re
import unicodedata

def _normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.lower()

_STOPWORDS = {
    'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'de', 'del', 'a', 'al', 'en',
    'por', 'para', 'con', 'sin', 'sobre', 'entre', 'hacia', 'hasta', 'y', 'e', 'ni', 'o',
    'u', 'pero', 'mas', 'que', 'como', 'cuando', 'donde', 'quien', 'cual', 'cuales',
    'cuyo', 'cuya', 'cuyos', 'cuyas',
    'informacion', 'tecnica', 'trabajo', 'trabajos', 'tenemos', 'registrado', 'registrados',
    'registrada', 'registradas', 'proyecto', 'proyectos', 'obra', 'obras', 'historial',
    'dime', 'cuentame', 'muestrame', 'ver', 'consultar', 'buscar', 'hay', 'existe', 'tienen',
    'saber', 'detalles', 'detalle', 'ficha', 'acerca'
}

def buscar_proyectos_por_texto(db: Session, query: str, limit: int = 10):
    """
    Búsqueda inteligente multi-estrategia en la base de datos de proyectos.
    Soporta:
    1. Búsqueda directa por ID (#1, proyecto 1, id 1).
    2. Filtrado por Estado ('ejecución', 'completado', 'planificado', 'estado de proyectos').
    3. Filtrado por Cliente / Categoría / Maquinaria / Ubicación.
    4. Extracción de frases entre comillas ("Montaje de Compresores en Planta Reficar").
    5. Normalización sin acentos y ponderación integral por relevancia.
    """
    if not query or not query.strip():
        return []

    query_lower = query.lower()
    query_norm = _normalizar_texto(query)

    # 1. Detección de ID explícito
    match_id = re.search(r'(?:#|proyecto\s+|id\s+)(\d+)', query_lower)
    if match_id:
        p_id = int(match_id.group(1))
        p = obtener_proyecto_por_id(db, p_id)
        if p:
            return [p]

    todos = db.query(Proyecto).all()
    if not todos:
        return []

    # 2. Detección explícita de Estado (Ejecución / Completado / Planificado)
    quiere_ejecucion = any(k in query_norm for k in ["ejecucion", "ejecutando", "ejecuta", "ejecutan", "en curso", "en progreso", "activos", "activo", "proceso", "desarrollo"])
    quiere_completado = any(k in query_norm for k in ["completado", "completados", "finalizado", "finalizados", "terminado", "terminados", "concluido", "concluidos", "cerrado", "cerrados"])
    quiere_planificado = any(k in query_norm for k in ["planificado", "planificados", "planeado", "planeados", "proyectado", "proyectados", "futuro", "futuros"])

    if quiere_ejecucion and not quiere_completado and not quiere_planificado:
        proyectos_ejec = [p for p in todos if p.estado and "ejecu" in _normalizar_texto(p.estado)]
        return proyectos_ejec

    if quiere_completado and not quiere_ejecucion:
        proyectos_comp = [p for p in todos if p.estado and "completa" in _normalizar_texto(p.estado)]
        return proyectos_comp[:max(limit, 25)]

    if quiere_planificado:
        proyectos_plan = [p for p in todos if p.estado and "planifica" in _normalizar_texto(p.estado)]
        return proyectos_plan

    # 3. Consulta general de estado de proyectos ("estado de los proyectos", "resumen de obras")
    if any(k in query_norm for k in ["estado de", "estados de", "en que estado", "resumen de proyectos"]):
        en_ejec = [p for p in todos if p.estado and "ejecu" in _normalizar_texto(p.estado)]
        otros = [p for p in todos if not (p.estado and "ejecu" in _normalizar_texto(p.estado))]
        return (en_ejec + otros)[:max(limit, 25)]

    # 4. Extracción de texto entre comillas si existe
    comillas = re.findall(r'["\'](.*?)["\']', query)
    frases_clave = [c.strip() for c in comillas if len(c.strip()) > 2]

    # 5. Normalizar y extraer palabras clave
    query_clean = re.sub(r'[^a-z0-9\s]', ' ', query_norm)
    palabras = [p for p in query_clean.split() if len(p) > 2 and p not in _STOPWORDS]

    if not palabras and not frases_clave:
        if any(w in query_norm for w in ["todos", "lista", "catalogo", "cuales son", "que proyectos"]):
            en_ejec = [p for p in todos if p.estado and "ejecu" in _normalizar_texto(p.estado)]
            otros = [p for p in todos if not (p.estado and "ejecu" in _normalizar_texto(p.estado))]
            return (en_ejec + otros)[:limit]
        return []

    puntuaciones = []

    for p in todos:
        score = 0
        t_norm = _normalizar_texto(p.titulo or "")
        c_norm = _normalizar_texto(p.cliente or "")
        u_norm = _normalizar_texto(p.ubicacion or "")
        m_norm = _normalizar_texto(p.maquinaria or "")
        d_norm = _normalizar_texto(p.descripcion or "")
        cat_norm = _normalizar_texto(p.categoria or "")
        e_norm = _normalizar_texto(p.estado or "")

        # A. Ponderación por coincidencia de frases entre comillas
        for f in frases_clave:
            f_norm = _normalizar_texto(f)
            if f_norm == t_norm:
                score += 200
            elif f_norm in t_norm:
                score += 150
            elif f_norm in c_norm or f_norm in d_norm or f_norm in m_norm:
                score += 80

        # B. Ponderación por palabras clave individuales
        palabras_encontradas = 0
        for palabra in palabras:
            hit = False
            if palabra in t_norm:
                score += 45
                hit = True
            if palabra in c_norm:
                score += 40
                hit = True
            if palabra in e_norm:
                score += 50
                hit = True
            if palabra in m_norm:
                score += 30
                hit = True
            if palabra in u_norm:
                score += 25
                hit = True
            if palabra in cat_norm:
                score += 20
                hit = True
            if palabra in d_norm:
                score += 15
                hit = True
            if hit:
                palabras_encontradas += 1

        # C. Bonus por ratio de coincidencia de palabras
        if palabras:
            ratio = palabras_encontradas / len(palabras)
            if ratio >= 0.75:
                score += 50
            elif ratio >= 0.5:
                score += 25

        if score >= 20:
            puntuaciones.append((score, p))

    puntuaciones.sort(key=lambda x: x[0], reverse=True)
    if not puntuaciones:
        return []

    top_score = puntuaciones[0][0]
    umbral = max(20, top_score * 0.35)
    filtrados = [item[1] for item in puntuaciones if item[0] >= umbral]
    return filtrados[:limit]

def actualizar_proyecto(db: Session, proyecto_id: int, datos: dict):
    proyecto = obtener_proyecto_por_id(db, proyecto_id)
    if not proyecto:
        return None
    for clave, valor in datos.items():
        if hasattr(proyecto, clave) and valor is not None:
            setattr(proyecto, clave, valor)
    db.commit()
    db.refresh(proyecto)
    return proyecto

def eliminar_proyecto(db: Session, proyecto_id: int) -> bool:
    proyecto = obtener_proyecto_por_id(db, proyecto_id)
    if not proyecto:
        return False
    db.delete(proyecto)
    db.commit()
    return True

def agregar_multimedia(db: Session, datos: dict) -> Multimedia:
    media = Multimedia(
        proyecto_id=datos.get("proyecto_id"),
        titulo=datos.get("titulo"),
        tipo=datos.get("tipo", "imagen"),
        archivo_url=datos.get("archivo_url"),
        seccion=datos.get("seccion", "galeria")
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media

def obtener_multimedia_por_proyecto(db: Session, proyecto_id: int):
    return db.query(Multimedia).filter(Multimedia.proyecto_id == proyecto_id).all()

# --- FUNCIONES PARA BLOG Y BANNER WEB ---
def crear_publicacion(db: Session, datos: dict) -> PublicacionBlog:
    pub = PublicacionBlog(
        proyecto_id=datos.get("proyecto_id"),
        titulo=datos.get("titulo"),
        resumen=datos.get("resumen"),
        contenido=datos.get("contenido"),
        multimedia_url=datos.get("multimedia_url"),
        tipo_multimedia=datos.get("tipo_multimedia", "imagen"),
        es_banner=1 if datos.get("es_banner", True) else 0,
        categoria=datos.get("categoria", "Noticias y Obras"),
        publicado=1 if datos.get("publicado", True) else 0,
        autor=datos.get("autor", "Equigrup")
    )
    db.add(pub)
    db.commit()
    db.refresh(pub)
    return pub

def obtener_publicaciones(db: Session, solo_banner: bool = False, limit: int = 100):
    query = db.query(PublicacionBlog)
    if solo_banner:
        query = query.filter(PublicacionBlog.es_banner == 1)
    return query.order_by(PublicacionBlog.creado_en.desc()).limit(limit).all()

def obtener_publicacion_por_id(db: Session, pub_id: int) -> PublicacionBlog | None:
    return db.query(PublicacionBlog).filter(PublicacionBlog.id == pub_id).first()

def actualizar_publicacion(db: Session, pub_id: int, datos: dict) -> PublicacionBlog | None:
    pub = obtener_publicacion_por_id(db, pub_id)
    if not pub:
        return None
    for clave, valor in datos.items():
        if hasattr(pub, clave) and valor is not None:
            if clave in ["es_banner", "publicado"] and isinstance(valor, bool):
                valor = 1 if valor else 0
            setattr(pub, clave, valor)
    db.commit()
    db.refresh(pub)
    return pub

def eliminar_publicacion(db: Session, pub_id: int) -> bool:
    pub = obtener_publicacion_por_id(db, pub_id)
    if not pub:
        return False
    db.delete(pub)
    db.commit()
    return True

def alternar_banner_publicacion(db: Session, pub_id: int) -> PublicacionBlog | None:
    pub = obtener_publicacion_por_id(db, pub_id)
    if not pub:
        return None
    pub.es_banner = 0 if pub.es_banner == 1 else 1
    db.commit()
    db.refresh(pub)
    return pub

# --- FUNCIONES DE SEGURIDAD, AUTENTICACIÓN Y RECUPERACIÓN DE CONTRASEÑA ---
import hashlib
import secrets
from datetime import datetime, timedelta

def hash_password(password: str) -> str:
    """Genera hash SHA-256 seguro con salt para almacenamiento persistente."""
    salt = "equigrup_auth_secure_2026_"
    return hashlib.sha256((salt + password.strip()).encode("utf-8")).hexdigest()

def verificar_password(password: str, password_hash: str) -> bool:
    """Verifica si la contraseña ingresada coincide con el hash guardado."""
    return hash_password(password) == password_hash

def crear_usuario_inicial_si_no_existe(db: Session) -> Usuario:
    """
    Garantiza que exista el usuario inicial requerido:
    Usuario: freddy | Contraseña: nico22 | Correo: freddy@equigrup.com
    """
    usuario = db.query(Usuario).filter(Usuario.username == "freddy").first()
    if not usuario:
        usuario = Usuario(
            username="freddy",
            email="freddy@equigrup.com",
            password_hash=hash_password("nico22"),
            nombre_completo="Freddy - Equigrup",
            rol="admin",
            activo=1
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        print("[SEGURIDAD] Usuario inicial 'freddy' creado exitosamente con contrasena 'nico22'.")
    return usuario

def verificar_login(db: Session, identificador: str, password: str) -> Usuario | None:
    """
    Verifica las credenciales de inicio de sesión por nombre de usuario o correo.
    """
    if not identificador or not password:
        return None
    ident_limpio = identificador.strip().lower()
    usuario = db.query(Usuario).filter(
        (Usuario.username.ilike(ident_limpio)) | (Usuario.email.ilike(ident_limpio))
    ).first()
    
    if usuario and usuario.activo and verificar_password(password, usuario.password_hash):
        return usuario
    return None

def generar_codigo_recuperacion(db: Session, email_o_user: str) -> tuple[str, str] | None:
    """
    Genera un código OTP de 6 dígitos para el correo asociado.
    Retorna (email_destino, codigo_6_digitos).
    """
    if not email_o_user:
        return None
    ident = email_o_user.strip().lower()
    
    # Buscar si corresponde a un usuario registrado
    usuario = db.query(Usuario).filter(
        (Usuario.username.ilike(ident)) | (Usuario.email.ilike(ident))
    ).first()
    
    email_destino = usuario.email if usuario else (ident if "@" in ident else "freddy@equigrup.com")
    
    # Generar código de 6 dígitos numéricos
    codigo = f"{secrets.randbelow(900000) + 100000}"
    expiracion = datetime.utcnow() + timedelta(minutes=15)
    
    # Inactivar códigos anteriores no usados para este correo
    db.query(CodigoRecuperacion).filter(
        CodigoRecuperacion.email.ilike(email_destino),
        CodigoRecuperacion.usado == 0
    ).update({"usado": 1}, synchronize_session=False)
    
    registro_codigo = CodigoRecuperacion(
        email=email_destino,
        codigo=codigo,
        expira_en=expiracion,
        usado=0
    )
    db.add(registro_codigo)
    db.commit()
    
    return email_destino, codigo

def validar_codigo_recuperacion(db: Session, email: str, codigo: str) -> bool:
    """
    Valida si el código de 6 dígitos está activo y no ha expirado.
    """
    if not email or not codigo:
        return False
    email_limpio = email.strip().lower()
    codigo_limpio = codigo.strip()
    
    ahora = datetime.utcnow()
    registro = db.query(CodigoRecuperacion).filter(
        CodigoRecuperacion.email.ilike(email_limpio),
        CodigoRecuperacion.codigo == codigo_limpio,
        CodigoRecuperacion.usado == 0,
        CodigoRecuperacion.expira_en > ahora
    ).first()
    
    return registro is not None

def cambiar_password_con_codigo(db: Session, email: str, codigo: str, nueva_password: str) -> bool:
    """
    Valida el código OTP, lo marca como usado y actualiza la contraseña del usuario en la BD.
    """
    if not validar_codigo_recuperacion(db, email, codigo):
        return False
    
    email_limpio = email.strip().lower()
    ahora = datetime.utcnow()
    
    # Marcar código como usado
    registro_codigo = db.query(CodigoRecuperacion).filter(
        CodigoRecuperacion.email.ilike(email_limpio),
        CodigoRecuperacion.codigo == codigo.strip(),
        CodigoRecuperacion.usado == 0,
        CodigoRecuperacion.expira_en > ahora
    ).first()
    
    if registro_codigo:
        registro_codigo.usado = 1
    
    # Actualizar la contraseña del usuario asociado
    usuario = db.query(Usuario).filter(
        (Usuario.email.ilike(email_limpio)) | (Usuario.username == "freddy")
    ).first()
    
    if usuario:
        usuario.password_hash = hash_password(nueva_password)
        db.commit()
        db.refresh(usuario)
        print(f"[SEGURIDAD] Contrasena actualizada exitosamente para el usuario '{usuario.username}'.")
        return True
    
    db.commit()
    return False
