from datetime import timedelta
from fastapi import FastAPI, Request, Depends, status, Form, Response, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.status import HTTP_400_BAD_REQUEST
from db import SessionLocal, engine, DBContext
import models, crud, schemas
from sqlalchemy.orm import Session
from fastapi_login import LoginManager
from dotenv import load_dotenv
import os
from passlib.context import CryptContext
from fastapi.responses import RedirectResponse ,JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
import uvicorn

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
ACCESS_TOKEN_EXPIRE_MINUTES=60

manager = LoginManager(SECRET_KEY, token_url="/login", use_cookie=True)
manager.cookie_name = "auth"

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

def get_db():
    with DBContext() as db:
        yield db

def get_hashed_password(plain_password):
    return pwd_ctx.hash(plain_password)

def verify_password(plain_password, hashed_password):
    return pwd_ctx.verify(plain_password,hashed_password)

@manager.user_loader()
def get_user(username: str, db: Session = None):
    if db is None:
        with DBContext() as db:
            return crud.get_user_by_username(db=db,username=username)
    return crud.get_user_by_username(db=db,username=username)

def authenticate_user(username: str, password: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db=db,username=username)
    if not user:
        return None
    if not verify_password(plain_password=password,hashed_password=user.hashed_password):
        return None
    return user

class NotAuthenticatedException(Exception):
    pass

def not_authenticated_exception_handler(request, exception):
    return RedirectResponse("/login")

manager.not_authenticated_exception = NotAuthenticatedException
app.add_exception_handler(NotAuthenticatedException, not_authenticated_exception_handler)

@app.get("/")
async def root(request: Request):
    return {"request":"ROOT"}


@app.post("/Register/user")
def Create_user(request: Request,
username: str = Form(...),
password: str = Form(...),
role : str = Form(...),
db: Session = Depends(get_db)):
    hashed_password = get_hashed_password(password)
    invalid = False
    if crud.get_user_by_username(db=db,username=username):
        invalid = True  
    if not invalid:
        crud.create_user(db=db,role=role,user=schemas.UserCreate(username=username,hashed_password=hashed_password))
        return {"Sign Up Successful"}

@app.post('/Login')
async def login(request: Request, 
form_data: OAuth2PasswordRequestForm = Depends(), 
db: Session = Depends(get_db)):
    user:schemas.User = authenticate_user(
        username=form_data.username,
        password = form_data.password, db = db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = manager.create_access_token(
        data={"sub": user.username},
        expires=access_token_expires)
    
    resp = JSONResponse(access_token, status_code=status.HTTP_200_OK)
    manager.set_cookie(resp,access_token)
    return resp
    
def role_admin(user:schemas.User = Depends(manager)):
    return user if user.role =='admin' else None

def role_normal(user:schemas.User = Depends(manager)):
    return user if (user.role =='admin' or user.role =='normal') else None
@app.get('/logout')
async def protected_route(request: Request, user:schemas.User=Depends(manager)):
    resp = JSONResponse({"status": "Logout Successful","user":user.username}, status_code=status.HTTP_200_OK)
    manager.delete_cookie(resp)
    return resp

@app.get("/Getlogin")
async def home(user: schemas.User = Depends(manager)):
    return user

@app.get("/Admin")
async def admin(request: Request, user: schemas.User = Depends(role_admin)):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission for this",
            headers={"WWW-Authorization": "Admin"},
        )
    return {"status":"Login with admin"}

@app.get("/Normal")
async def normal(user: schemas.User = Depends(role_admin)):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission for this",
            headers={"WWW-Authorization": "Nomal"},
        )
    return {"status":"Login Successful"}

# import jwt
# @app.post("/load_token", tags=['token'])
# async def load_token(token:str=Form(...)):
#     pay = jwt.decode(
#                 token, SECRET_KEY, algorithms=["HS256"]
#             )
#     return pay

if __name__=="__main__":
    uvicorn.run(app)