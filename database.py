from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from config import Config

engine = create_engine(Config.DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Bot(Base):
    __tablename__ = "bots"
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer)
    token = Column(String)
    username = Column(String)
    repo_name = Column(String)
    status = Column(String)  # running / stopped
    language = Column(String, default="fa")

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    bot_id = Column(Integer)
    content = Column(Text)

Base.metadata.create_all(engine)
