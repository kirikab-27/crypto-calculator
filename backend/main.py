import sys
import os
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import json

from src.auth import hash_password, verify_password
from src.db import create_user, authenticate_user, get_db_connection
from src.calculator import CryptoCalculator
from src.csv_import import import_csv
from src.reporting import generate_report

# Configuration
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Crypto Calculator API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Transaction(BaseModel):
    date: str
    type: str  # "buy" or "sell"
    currency: str
    amount: float
    price: float
    fee: float = 0.0

class TransactionList(BaseModel):
    transactions: List[Transaction]

class CalculateRequest(BaseModel):
    transactions: List[Transaction]
    method: str = "fifo"  # "fifo" or "lifo"

class ImportCSVRequest(BaseModel):
    content: str
    source: str = "generic"  # "generic", "binance", "mexc"

# Utility functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Check if user exists
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user is None:
        raise credentials_exception
    return User(username=username)

# Routes
@app.get("/")
def read_root():
    return {"message": "Crypto Calculator API"}

@app.post("/api/register", response_model=User)
def register(user: UserCreate):
    try:
        create_user(user.username, user.password)
        return User(username=user.username)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/api/calculate")
async def calculate_gains(
    request: CalculateRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        calculator = CryptoCalculator(method=request.method)
        
        # Process transactions
        for tx in request.transactions:
            tx_date = datetime.strptime(tx.date, "%Y-%m-%d")
            if tx.type == "buy":
                calculator.add_buy(tx_date, tx.currency, tx.amount, tx.price, tx.fee)
            elif tx.type == "sell":
                calculator.add_sell(tx_date, tx.currency, tx.amount, tx.price, tx.fee)
        
        # Calculate gains/losses
        summary = calculator.calculate_summary()
        transactions = calculator.get_all_transactions()
        
        return {
            "summary": summary,
            "transactions": [
                {
                    "date": tx.date.strftime("%Y-%m-%d"),
                    "type": tx.type,
                    "currency": tx.currency,
                    "amount": tx.amount,
                    "price": tx.price,
                    "fee": tx.fee,
                    "gain_loss": getattr(tx, "gain_loss", None)
                }
                for tx in transactions
            ],
            "inventory": calculator.get_inventory_status()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/import-csv")
async def import_csv_endpoint(
    request: ImportCSVRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        # Save content to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(request.content)
            temp_path = f.name
        
        # Import transactions
        transactions = import_csv(temp_path, source=request.source)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        return {
            "message": f"Successfully imported {len(transactions)} transactions",
            "transactions": [
                {
                    "date": tx.date.strftime("%Y-%m-%d"),
                    "type": tx.type,
                    "currency": tx.currency,
                    "amount": tx.amount,
                    "price": tx.price,
                    "fee": tx.fee
                }
                for tx in transactions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/generate-report")
async def generate_report_endpoint(
    request: CalculateRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        calculator = CryptoCalculator(method=request.method)
        
        # Process transactions
        for tx in request.transactions:
            tx_date = datetime.strptime(tx.date, "%Y-%m-%d")
            if tx.type == "buy":
                calculator.add_buy(tx_date, tx.currency, tx.amount, tx.price, tx.fee)
            elif tx.type == "sell":
                calculator.add_sell(tx_date, tx.currency, tx.amount, tx.price, tx.fee)
        
        # Generate report
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        generate_report(calculator, temp_path, format="csv")
        
        # Read report content
        with open(temp_path, 'r') as f:
            content = f.read()
        
        # Clean up
        os.unlink(temp_path)
        
        return {
            "content": content,
            "format": "csv",
            "summary": calculator.calculate_summary()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/exchanges")
async def get_exchanges(current_user: User = Depends(get_current_user)):
    return {
        "exchanges": [
            {"id": "binance", "name": "Binance", "status": "available"},
            {"id": "mexc", "name": "MEXC", "status": "available"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)