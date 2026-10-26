from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base

class Proyecto(Base):
    __tablename__ = "proyectos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False, index=True)
    cliente = Column(String(150), nullable=True)
    ubicacion = Column(String(150), nullable=True)
    categoria = Column(String(100), nullable=True) # Ej: Instalación, Mantenimiento, Montaje
    estado = Column(String(50), default="En ejecución") # En ejecución, Completado, Planificado
    maquinaria = Column(String(200), nullable=True) # Ej: Compresores reciprocantes, Bombas API
    descripcion = Column(Text, nullable=True)
    imagen_url = Column(String(500), nullable=True)
    creado_por = Column(String(100), default="Freddy")
    creado_en = Column(DateTime, default=datetime.utcnow)

    # Relación con archivos multimedia
    multimedia = relationship("Multimedia", back_populates="proyecto", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "cliente": self.cliente or "",
            "ubicacion": self.ubicacion or "",
            "categoria": self.categoria or "General",
            "estado": self.estado or "En ejecución",
            "maquinaria": self.maquinaria or "",
            "descripcion": self.descripcion or "",
            "imagen_url": self.imagen_url or "",
            "creado_por": self.creado_por or "Admin",
            "creado_en": self.creado_en.strftime("%Y-%m-%d %H:%M") if self.creado_en else "",
            "multimedia": [m.to_dict() for m in self.multimedia] if self.multimedia else []
        }

class Multimedia(Base):
    __tablename__ = "multimedia"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=True)
    titulo = Column(String(150), nullable=True)
    tipo = Column(String(50), default="imagen") # imagen, plano, pdf, video
    archivo_url = Column(String(500), nullable=False)
    seccion = Column(String(100), default="galeria") # galeria, portada, documentos
    subido_en = Column(DateTime, default=datetime.utcnow)

    proyecto = relationship("Proyecto", back_populates="multimedia")

    def to_dict(self):
        return {
            "id": self.id,
            "proyecto_id": self.proyecto_id,
            "titulo": self.titulo or "",
            "tipo": self.tipo,
            "archivo_url": self.archivo_url,
            "seccion": self.seccion,
            "subido_en": self.subido_en.strftime("%Y-%m-%d %H:%M") if self.subido_en else ""
        }

class PublicacionBlog(Base):
    __tablename__ = "publicaciones_blog"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=True)
    titulo = Column(String(250), nullable=False)
    resumen = Column(String(500), nullable=True) # Resumen corto para banner
    contenido = Column(Text, nullable=False) # Descripción o artículo completo
    multimedia_url = Column(String(500), nullable=True) # URL de imagen o video
    tipo_multimedia = Column(String(50), default="imagen") # imagen, video
    es_banner = Column(Integer, default=1) # 1 si se destaca en el banner principal, 0 si no
    categoria = Column(String(100), default="Noticias y Obras")
    publicado = Column(Integer, default=1) # 1 publicado, 0 borrador
    autor = Column(String(100), default="Equigrup")
    creado_en = Column(DateTime, default=datetime.utcnow)

    proyecto = relationship("Proyecto")

    def to_dict(self):
        return {
            "id": self.id,
            "proyecto_id": self.proyecto_id,
            "titulo": self.titulo,
            "resumen": self.resumen or "",
            "contenido": self.contenido or "",
            "multimedia_url": self.multimedia_url or "",
            "tipo_multimedia": self.tipo_multimedia or "imagen",
            "es_banner": bool(self.es_banner),
            "categoria": self.categoria or "Noticias y Obras",
            "publicado": bool(self.publicado),
            "autor": self.autor or "Equigrup",
            "creado_en": self.creado_en.strftime("%Y-%m-%d %H:%M") if self.creado_en else "",
            "proyecto_titulo": self.proyecto.titulo if self.proyecto else None
        }

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre_completo = Column(String(150), default="Freddy")
    rol = Column(String(50), default="admin")
    activo = Column(Integer, default=1)
    creado_en = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "nombre_completo": self.nombre_completo,
            "rol": self.rol,
            "activo": bool(self.activo),
            "creado_en": self.creado_en.strftime("%Y-%m-%d %H:%M") if self.creado_en else ""
        }

class CodigoRecuperacion(Base):
    __tablename__ = "codigos_recuperacion"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), nullable=False, index=True)
    codigo = Column(String(10), nullable=False)
    expira_en = Column(DateTime, nullable=False)
    usado = Column(Integer, default=0)
    creado_en = Column(DateTime, default=datetime.utcnow)
