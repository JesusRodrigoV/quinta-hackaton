from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    Clase base declarativa moderna de SQLAlchemy 2.0.
    Todos los modelos del microservicio heredarán de este molde maestro
    para permitir el mapeo automático de tablas y el rastreo de Alembic.
    """
    pass