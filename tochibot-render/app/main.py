import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, select
from sqlalchemy.orm import declarative_base, sessionmaker, Session

BASE = Path(__file__).resolve().parent
url = os.getenv('DATABASE_URL', 'sqlite:///./tochibot.db')
if url.startswith('postgres://'):
    url = 'postgresql://' + url[len('postgres://'):]
if url.startswith('postgresql://') and '+psycopg' not in url:
    url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
engine = create_engine(url, pool_pre_ping=True, connect_args={'check_same_thread': False} if url.startswith('sqlite:') else {})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
secret = os.getenv('SECRET_KEY', '')
if not secret:
    if os.getenv('RENDER'):
        raise RuntimeError('SECRET_KEY must be configured in production')
    secret = secrets.token_urlsafe(32)
pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    title = Column(String(240), nullable=False)
    due_date = Column(String(32))
    done = Column(Integer, default=0, nullable=False)

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    role = Column(String(12), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(engine)
app = FastAPI(title='TochiBOT', version='1.0.0')
app.mount('/static', StaticFiles(directory=str(BASE / 'static')), name='static')

def db_session():
    with SessionLocal() as db:
        yield db

def current_user(authorization: str | None = Header(default=None), db: Session = Depends(db_session)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, 'Authentication required')
    try:
        payload = jwt.decode(authorization[7:], secret, algorithms=['HS256'])
        uid = int(payload['sub'])
    except (JWTError, ValueError, KeyError):
        raise HTTPException(401, 'Invalid or expired token')
    user = db.get(User, uid)
    if not user:
        raise HTTPException(401, 'Account not found')
    return user

class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    due_date: str | None = Field(default=None, max_length=32)

class TaskPatch(BaseModel):
    done: bool

class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

def token_for(user):
    return jwt.encode({'sub': str(user.id), 'exp': datetime.now(timezone.utc) + timedelta(days=7)}, secret, algorithm='HS256')

@app.get('/')
def home():
    return FileResponse(BASE / 'static' / 'index.html')

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/api/register')
def register(data: Credentials, db: Session = Depends(db_session)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, 'Email already registered')
    user = User(email=email, password_hash=pwd.hash(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {'token': token_for(user), 'email': user.email}

@app.post('/api/login')
def login(data: Credentials, db: Session = Depends(db_session)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not pwd.verify(data.password, user.password_hash):
        raise HTTPException(401, 'Incorrect email or password')
    return {'token': token_for(user), 'email': user.email}

@app.get('/api/me')
def me(user: User = Depends(current_user)):
    return {'email': user.email}

@app.get('/api/tasks')
def tasks(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.scalars(select(Task).where(Task.user_id == user.id).order_by(Task.id.desc())).all()
    return [{'id': x.id, 'title': x.title, 'due_date': x.due_date, 'done': bool(x.done)} for x in rows]

@app.post('/api/tasks')
def create_task(data: TaskIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    task = Task(user_id=user.id, title=data.title.strip(), due_date=data.due_date)
    if not task.title:
        raise HTTPException(422, 'Title required')
    db.add(task)
    db.commit()
    return {'id': task.id}

@app.patch('/api/tasks/{task_id}')
def update_task(task_id: int, data: TaskPatch, user: User = Depends(current_user), db: Session = Depends(db_session)):
    task = db.get(Task, task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(404, 'Task not found')
    task.done = int(data.done)
    db.commit()
    return {'ok': True}

@app.delete('/api/tasks/{task_id}')
def delete_task(task_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
    task = db.get(Task, task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(404, 'Task not found')
    db.delete(task)
    db.commit()
    return {'ok': True}

@app.get('/api/messages')
def messages(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.scalars(select(Message).where(Message.user_id == user.id).order_by(Message.id.desc()).limit(50)).all()
    return [{'role': m.role, 'content': m.content} for m in reversed(rows)]

@app.post('/api/chat')
async def chat(data: ChatIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        raise HTTPException(503, 'AI chat is not configured; add OPENAI_API_KEY on Render')
    history = db.scalars(select(Message).where(Message.user_id == user.id).order_by(Message.id.desc()).limit(18)).all()
    pending = [{'role': m.role, 'content': m.content} for m in reversed(history)]
    pending.append({'role': 'user', 'content': data.message})
    own_tasks = db.scalars(select(Task).where(Task.user_id == user.id, Task.done == 0).limit(20)).all()
    task_context = '; '.join(t.title for t in own_tasks)[:1200]
    body = {'model': os.getenv('OPENAI_MODEL', 'gpt-4.1-mini'), 'messages': [
        {'role': 'system', 'content': 'You are TochiBOT, a supportive and practical productivity assistant. Be accurate and concise. Do not claim to have taken actions you did not take. Open tasks: ' + task_context}, *pending], 'max_tokens': 600}
    try:
        async with httpx.AsyncClient(timeout=35) as client:
            response = await client.post('https://api.openai.com/v1/chat/completions', headers={'Authorization': 'Bearer ' + key}, json=body)
            response.raise_for_status()
            answer = response.json()['choices'][0]['message']['content']
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        raise HTTPException(502, 'AI service is temporarily unavailable')
    db.add_all([Message(user_id=user.id, role='user', content=data.message), Message(user_id=user.id, role='assistant', content=answer)])
    db.commit()
    return {'reply': answer}
