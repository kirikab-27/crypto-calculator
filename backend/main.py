import sys
import os
from pathlib import Path
import sqlite3

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
from src.db import create_user, authenticate_user, get_db_connection, init_db, add_transaction, get_user_transactions, get_user_transactions_filtered, get_user_currencies, delete_transaction, update_transaction, get_user_by_username, remove_duplicate_transactions, check_transaction_exists
from src.calculator import CryptoCalculator
from src.csv_import import import_csv
from src.reporting import generate_csv_report
from src.tax_report import generate_tax_summary_report, TaxReportGenerator

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
    id: Optional[int] = None

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
    id: Optional[int] = None
    gain_loss: Optional[float] = None

class TransactionList(BaseModel):
    transactions: List[Transaction]

class CalculateRequest(BaseModel):
    transactions: List[Transaction]
    method: str = "fifo"  # "fifo" or "lifo"

class ImportCSVRequest(BaseModel):
    content: str
    source: str = "generic"  # "generic", "binance", "mexc"

class TaxReportRequest(BaseModel):
    method: str = "FIFO"  # "FIFO" or "LIFO"
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None  # YYYY-MM-DD
    format: str = "json"  # "json", "csv", "pdf"

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
    
    # Check if user exists and get full user data
    user = get_user_by_username(username)
    
    if user is None:
        raise credentials_exception
    return User(username=user.username, id=user.id)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

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
        
        # Sort transactions by date before processing to ensure chronological order
        sorted_transactions = sorted(request.transactions, key=lambda tx: tx.date)
        
        # Process transactions
        for tx in sorted_transactions:
            tx_date = datetime.strptime(tx.date, "%Y-%m-%d")
            if tx.type == "buy":
                calculator.add_buy(tx_date, tx.currency, tx.amount, tx.price, tx.fee)
            elif tx.type == "sell":
                calculator.add_sell(tx_date, tx.currency, tx.amount, tx.price, tx.fee)
        
        # Calculate gains/losses
        summary = calculator.calculate_summary()
        transactions = calculator.get_all_transactions()
        
        # Transform summary to match frontend expectations
        total_gain_loss = summary.get("total_gain_loss", 0)
        transformed_summary = {
            "total_realized_gains": max(0, total_gain_loss),
            "total_realized_losses": min(0, total_gain_loss),
            "net_gain_loss": total_gain_loss,
            "transactions_count": len(transactions)
        }
        
        # Transform inventory to match frontend expectations
        inventory = calculator.get_inventory_status()
        transformed_inventory = {}
        for currency, data in inventory.items():
            transformed_inventory[currency] = {
                "total_amount": data["amount"],
                "average_price": data["average_cost"]
            }
        
        return {
            "summary": transformed_summary,
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
            "inventory": transformed_inventory
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
        
        # Save transactions to database, skipping duplicates
        saved_transactions = []
        skipped_duplicates = 0
        for tx in transactions:
            # Check if transaction already exists
            if check_transaction_exists(
                user_id=current_user.id,
                date=tx.date.strftime("%Y-%m-%d"),
                type=tx.type,
                currency=tx.currency,
                amount=tx.amount,
                price=tx.price,
                fee=tx.fee
            ):
                skipped_duplicates += 1
                continue
            
            tx_id = add_transaction(
                user_id=current_user.id,
                date=tx.date.strftime("%Y-%m-%d"),
                type=tx.type,
                currency=tx.currency,
                amount=tx.amount,
                price=tx.price,
                fee=tx.fee
            )
            saved_transactions.append({
                "id": tx_id,
                "date": tx.date.strftime("%Y-%m-%d"),
                "type": tx.type,
                "currency": tx.currency,
                "amount": tx.amount,
                "price": tx.price,
                "fee": tx.fee
            })
        
        message = f"Successfully imported {len(saved_transactions)} transactions"
        if skipped_duplicates > 0:
            message += f" (skipped {skipped_duplicates} duplicates)"
        
        return {
            "message": message,
            "transactions": saved_transactions,
            "skipped_duplicates": skipped_duplicates
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
        
        # Sort transactions by date before processing to ensure chronological order
        sorted_transactions = sorted(request.transactions, key=lambda tx: tx.date)
        
        # Process transactions
        for tx in sorted_transactions:
            tx_date = datetime.strptime(tx.date, "%Y-%m-%d")
            if tx.type == "buy":
                calculator.add_buy(tx_date, tx.currency, tx.amount, tx.price, tx.fee)
            elif tx.type == "sell":
                calculator.add_sell(tx_date, tx.currency, tx.amount, tx.price, tx.fee)
        
        # Generate report
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        summary = calculator.calculate_summary()
        generate_csv_report(summary, temp_path)
        
        # Read report content
        with open(temp_path, 'r') as f:
            content = f.read()
        
        # Clean up
        os.unlink(temp_path)
        
        return {
            "content": content,
            "format": "csv",
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Transaction management endpoints
@app.post("/api/transactions", response_model=Transaction)
async def create_transaction(
    transaction: Transaction,
    current_user: User = Depends(get_current_user)
):
    """Save a new transaction to the database."""
    try:
        # Check if transaction already exists
        if check_transaction_exists(
            user_id=current_user.id,
            date=transaction.date,
            type=transaction.type,
            currency=transaction.currency,
            amount=transaction.amount,
            price=transaction.price,
            fee=transaction.fee
        ):
            raise HTTPException(
                status_code=400, 
                detail="A transaction with identical details already exists. Please check your transaction list or use the 'Remove Duplicates' button."
            )
        
        transaction_id = add_transaction(
            user_id=current_user.id,
            date=transaction.date,
            type=transaction.type,
            currency=transaction.currency,
            amount=transaction.amount,
            price=transaction.price,
            fee=transaction.fee,
            gain_loss=transaction.gain_loss
        )
        transaction.id = transaction_id
        return transaction
    except HTTPException:
        raise
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=400,
                detail="This transaction already exists. Please check your transaction list or use the 'Remove Duplicates' button."
            )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/transactions", response_model=List[Transaction])
async def get_transactions(current_user: User = Depends(get_current_user)):
    """Get all transactions for the current user."""
    try:
        transactions = get_user_transactions(current_user.id)
        return [
            Transaction(
                id=tx["id"],
                date=tx["date"],
                type=tx["type"],
                currency=tx["currency"],
                amount=tx["amount"],
                price=tx["price"],
                fee=tx["fee"],
                gain_loss=tx["gain_loss"]
            )
            for tx in transactions
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction_endpoint(
    transaction_id: int,
    transaction: Transaction,
    current_user: User = Depends(get_current_user)
):
    """Update a transaction if it belongs to the current user."""
    try:
        if update_transaction(
            user_id=current_user.id,
            transaction_id=transaction_id,
            date=transaction.date,
            type=transaction.type,
            currency=transaction.currency,
            amount=transaction.amount,
            price=transaction.price,
            fee=transaction.fee,
            gain_loss=transaction.gain_loss
        ):
            transaction.id = transaction_id
            return transaction
        else:
            raise HTTPException(status_code=404, detail="Transaction not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/transactions/{transaction_id}")
async def delete_transaction_endpoint(
    transaction_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a transaction if it belongs to the current user."""
    try:
        if delete_transaction(current_user.id, transaction_id):
            return {"message": "Transaction deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Transaction not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class TransactionsFilteredResponse(BaseModel):
    transactions: List[Transaction]
    total: int
    limit: int
    offset: int

@app.get("/api/transactions/filtered", response_model=TransactionsFilteredResponse)
async def get_transactions_filtered(
    limit: int = 10,
    offset: int = 0,
    type: Optional[str] = None,
    currency: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get filtered transactions with pagination."""
    # Debug logging for date filter issue
    print(f"[Backend Debug] Raw params - start_date: '{start_date}', end_date: '{end_date}', type: '{type}', currency: '{currency}'")
    
    # Validate date format if provided
    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid start_date format. Expected YYYY-MM-DD, got: {start_date}")
    
    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid end_date format. Expected YYYY-MM-DD, got: {end_date}")
    
    try:
        result = get_user_transactions_filtered(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            type_filter=type,
            currency_filter=currency,
            start_date=start_date,
            end_date=end_date
        )
        
        return TransactionsFilteredResponse(
            transactions=[
                Transaction(
                    id=tx["id"],
                    date=tx["date"],
                    type=tx["type"],
                    currency=tx["currency"],
                    amount=tx["amount"],
                    price=tx["price"],
                    fee=tx["fee"],
                    gain_loss=tx["gain_loss"]
                )
                for tx in result["transactions"]
            ],
            total=result["total"],
            limit=result["limit"],
            offset=result["offset"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/currencies", response_model=List[str])
async def get_currencies(current_user: User = Depends(get_current_user)):
    """Get distinct currencies used in user's transactions."""
    try:
        return get_user_currencies(current_user.id)
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

@app.post("/api/transactions/remove-duplicates")
async def remove_duplicates(current_user: User = Depends(get_current_user)):
    """Remove duplicate transactions for the current user."""
    try:
        duplicates_removed = remove_duplicate_transactions(current_user.id)
        return {
            "message": f"Successfully removed {duplicates_removed} duplicate transactions",
            "duplicates_removed": duplicates_removed
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/tax-summary-report")
async def generate_tax_summary_report_endpoint(
    request: TaxReportRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate a comprehensive tax summary report."""
    try:
        # Generate the report
        report = generate_tax_summary_report(
            user_id=current_user.id,
            method=request.method,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Return based on requested format
        if request.format == "json":
            # Get transactions for the report
            transactions = get_user_transactions(current_user.id)
            generator = TaxReportGenerator(transactions, request.method, request.start_date, request.end_date)
            json_content = generator.export_json(report)
            return {
                "format": "json",
                "content": json.loads(json_content),
                "filename": f"tax_summary_{report.report_period_start}_{report.report_period_end}.json"
            }
            
        elif request.format == "csv":
            # Generate CSV
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
                temp_path = f.name
            
            transactions = get_user_transactions(current_user.id)
            generator = TaxReportGenerator(transactions, request.method, request.start_date, request.end_date)
            generator.export_csv(report, temp_path)
            
            # Read content
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean up
            os.unlink(temp_path)
            
            return {
                "format": "csv",
                "content": content,
                "filename": f"tax_summary_{report.report_period_start}_{report.report_period_end}.csv"
            }
            
        elif request.format == "pdf":
            # Generate PDF
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
                temp_path = f.name
            
            transactions = get_user_transactions(current_user.id)
            generator = TaxReportGenerator(transactions, request.method, request.start_date, request.end_date)
            generator.export_pdf(report, temp_path)
            
            # Read content (as base64 for PDF)
            import base64
            with open(temp_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            
            # Clean up
            os.unlink(temp_path)
            
            return {
                "format": "pdf",
                "content": content,
                "filename": f"tax_summary_{report.report_period_start}_{report.report_period_end}.pdf",
                "is_base64": True
            }
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tax-summary-report/preview")
async def preview_tax_summary_report(
    method: str = "FIFO",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get a preview of the tax summary report data."""
    try:
        # Generate the report
        report = generate_tax_summary_report(
            user_id=current_user.id,
            method=method,
            start_date=start_date,
            end_date=end_date
        )
        
        # Convert to dict for preview
        from dataclasses import asdict
        report_dict = asdict(report)
        
        return {
            "preview": report_dict,
            "available_formats": ["json", "csv", "pdf"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)