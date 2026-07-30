# main.py
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import openai
import chromadb
from chromadb.utils import embedding_functions
import json
import os
import base64
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURAZIONE
# ==========================================

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("ERRORE: Non ho trovato la OPENAI_API_KEY nel file .env!")

openai.api_key = api_key

# Configurazione JWT
SECRET_KEY = "tua_chiave_segreta_super_sicura_cambiala_in_produzione_12345"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Security
security = HTTPBearer()

# ==========================================
# 2. PERCORSI
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "utenti.json")
CRONOLOGIA_FILE = os.path.join(BASE_DIR, "cronologia_analisi.json")

# ==========================================
# 3. FASTAPI
# ==========================================

app = FastAPI(
    title="FiscoHunter AI Backend",
    description="Il motore di ragionamento fiscale.",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 4. FUNZIONI UTENTI
# ==========================================

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenziali non valide",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    users = load_users()
    user = users.get(email)
    if user is None:
        raise credentials_exception
    return user

# ==========================================
# 5. MODELLI
# ==========================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    nome: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProfiloUtente(BaseModel):
    regime_fiscale: str
    reddito_complessivo: float
    aliquota_marginale: float

class RichiestaAnalisi(BaseModel):
    profilo: ProfiloUtente
    spesa_descrizione: str
    importo_spesa: float

class RispostaFiscale(BaseModel):
    obiettivo: str
    vantaggio_economico: str
    riferimento_normativo: str
    cavillo_strategia: str
    rischi_controlli: str
    azione_immediata: str

class AnalisiCompleta(BaseModel):
    profilo: ProfiloUtente
    spesa_descrizione: str
    importo_spesa: float
    obiettivo: str
    vantaggio_economico: str
    riferimento_normativo: str
    cavillo_strategia: str
    rischi_controlli: str
    azione_immediata: str

# ==========================================
# 6. CHROMADB
# ==========================================

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=openai.api_key,
    model_name="text-embedding-3-small"
)

chroma_client = chromadb.PersistentClient(path=os.path.join(BASE_DIR, "chroma_db"))
fisco_collection = chroma_client.get_or_create_collection(
    name="normativa_fiscale_italiana",
    embedding_function=openai_ef
)

# ==========================================
# 7. SYSTEM PROMPT
# ==========================================

SYSTEM_PROMPT = """
Sei FiscoHunter AI, esperto ottimizzatore fiscale italiano.
Rispondi sempre in JSON con: obiettivo, vantaggio_economico, riferimento_normativo, cavillo_strategia, rischi_controlli, azione_immediata
"""

# ==========================================
# 8. DATABASE BONUS
# ==========================================

BONUS_DATABASE = [
    {
        "id": "ecobonus_65",
        "documento": "Ecobonus 65% per climatizzatori e pompe di calore. Art. 1, commi 345-347, Legge 296/2006.",
        "metadati": {"categoria": "casa", "aliquota": "65%"}
    },
    {
        "id": "bonus_ristrutturazioni_50",
        "documento": "Bonus Ristrutturazioni 50% per manutenzione straordinaria. Art. 16-bis del TUIR.",
        "metadati": {"categoria": "casa", "aliquota": "50%"}
    },
    {
        "id": "detrazioni_sanitarie_19",
        "documento": "Detrazioni spese sanitarie 19% sopra franchigia 129,11€. Art. 15 TUIR.",
        "metadati": {"categoria": "salute", "aliquota": "19%"}
    },
    {
        "id": "bonus_nido_3000",
        "documento": "Bonus Nido fino a 3.000€ per asili nido. Art. 1, comma 355, Legge 232/2016.",
        "metadati": {"categoria": "famiglia", "massimale": 3000}
    },
    {
        "id": "fondo_pensione",
        "documento": "Fondi Pensione deducibili fino a 5.164,57€. Art. 10 TUIR.",
        "metadati": {"categoria": "investimenti", "massimale": 5164.57}
    },
]

# ==========================================
# 9. FUNZIONI MOTORE
# ==========================================

def popola_database_completo():
    if fisco_collection.count() == 0:
        print("📚 Popolamento database...")
        documenti = [bonus["documento"] for bonus in BONUS_DATABASE]
        ids = [bonus["id"] for bonus in BONUS_DATABASE]
        metadati_puliti = [{k: v for k, v in b["metadati"].items() if v is not None} for b in BONUS_DATABASE]
        fisco_collection.add(documents=documenti, metadatas=metadati_puliti, ids=ids)
        print(f"✅ Database popolato: {len(BONUS_DATABASE)} bonus")

def cerca_normativa_pertinente(testo_ricerca: str, n_risultati: int = 3):
    results = fisco_collection.query(query_texts=[testo_ricerca], n_results=n_risultati)
    return results['documents'][0]

def genera_consiglio_fiscale(profilo: ProfiloUtente, spesa: str, importo: float, leggi_recuperate: List[str]) -> dict:
    contesto_leggi = "\n---\n".join(leggi_recuperate)
    user_prompt = f"PROFILO: {profilo.regime_fiscale}, Reddito: {profilo.reddito_complessivo}€, SPESA: {spesa} - {importo}€, CONTESTO: {contesto_leggi}"
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1000
    )
    return json.loads(response.choices[0].message.content)

def carica_cronologia(email_utente: str):
    try:
        if os.path.exists(CRONOLOGIA_FILE):
            with open(CRONOLOGIA_FILE, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
                return all_data.get(email_utente, [])
        return []
    except Exception as e:
        print(f" Errore carica cronologia: {e}")
        return []

def salva_cronologia(email_utente: str, cronologia):
    try:
        if os.path.exists(CRONOLOGIA_FILE):
            with open(CRONOLOGIA_FILE, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        else:
            all_data = {}
        all_data[email_utente] = cronologia
        with open(CRONOLOGIA_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Errore salva cronologia: {e}")

# ==========================================
# 10. ENDPOINT AUTH
# ==========================================

@app.post("/register")
async def register(user: UserRegister):
    users = load_users()
    if user.email in users:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    hashed_password = get_password_hash(user.password)
    users[user.email] = {
        "email": user.email,
        "password": hashed_password,
        "nome": user.nome,
        "created_at": datetime.now().isoformat()
    }
    save_users(users)
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"email": user.email, "nome": user.nome}
    }

@app.post("/login")
async def login(user: UserLogin):
    users = load_users()
    user_data = users.get(user.email)
    if not user_data or not verify_password(user.password, user_data["password"]):
        raise HTTPException(status_code=401, detail="Credenziali errate")
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"email": user_data["email"], "nome": user_data["nome"]}
    }

@app.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"email": current_user["email"], "nome": current_user["nome"]}

# ==========================================
# 11. ENDPOINT PRINCIPALI
# ==========================================

@app.on_event("startup")
async def startup_event():
    popola_database_completo()
    print(" FiscoHunter AI Backend pronto!")

@app.get("/")
async def root():
    return {"message": "FiscoHunter AI Backend", "status": "active"}

@app.post("/analisi")
async def analizzare_spesa(request: RichiestaAnalisi, current_user: dict = Depends(get_current_user)):
    try:
        leggi_pertinenti = cerca_normativa_pertinente(request.spesa_descrizione)
        consiglio = genera_consiglio_fiscale(
            profilo=request.profilo,
            spesa=request.spesa_descrizione,
            importo=request.importo_spesa,
            leggi_recuperate=leggi_pertinenti
        )
        return RispostaFiscale(**consiglio)
    except Exception as e:
        print(f" Errore analisi: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/salva-analisi")
async def salva_analisi(analisi: AnalisiCompleta, current_user: dict = Depends(get_current_user)):
    try:
        cronologia = carica_cronologia(current_user["email"])
        nuova_analisi = {
            "id": len(cronologia) + 1,
            "data": datetime.now().isoformat(),
            "profilo": {
                "regime_fiscale": analisi.profilo.regime_fiscale,
                "reddito_complessivo": analisi.profilo.reddito_complessivo,
                "aliquota_marginale": analisi.profilo.aliquota_marginale
            },
            "spesa": {
                "descrizione": analisi.spesa_descrizione,
                "importo": analisi.importo_spesa
            },
            "consiglio": {
                "obiettivo": analisi.obiettivo,
                "vantaggio_economico": analisi.vantaggio_economico,
                "riferimento_normativo": analisi.riferimento_normativo,
                "cavillo_strategia": analisi.cavillo_strategia,
                "rischi_controlli": analisi.rischi_controlli,
                "azione_immediata": analisi.azione_immediata
            }
        }
        cronologia.append(nuova_analisi)
        salva_cronologia(current_user["email"], cronologia)
        return {"success": True, "id": nuova_analisi["id"]}
    except Exception as e:
        print(f"❌ Errore salva analisi: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cronologia")
async def get_cronologia(current_user: dict = Depends(get_current_user)):
    try:
        cronologia = carica_cronologia(current_user["email"])
        return {"success": True, "analisi": cronologia, "totale": len(cronologia)}
    except Exception as e:
        print(f"❌ Errore get cronologia: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/statistiche")
async def get_statistiche(current_user: dict = Depends(get_current_user)):
    try:
        cronologia = carica_cronologia(current_user["email"])
        if not cronologia:
            return {"success": True, "totale_analisi": 0, "risparmio_totale": 0, "risparmio_mensile": {}, "categorie": {}, "media_risparmio": 0}
        
        risparmio_totale = 0
        risparmio_mensile = {}
        categorie = {}
        risparmi = []
        
        for analisi in cronologia:
            try:
                vantaggio = analisi['consiglio']['vantaggio_economico'] or ''
                import re
                match = re.search(r'[\d,]+\.?\d*', vantaggio)
                if match:
                    numero = match.group().replace(',', '.')
                    risparmio = float(numero)
                    risparmi.append(risparmio)
                    risparmio_totale += risparmio
                    data = analisi.get('data', '')
                    if data:
                        mese = data[:7]
                        risparmio_mensile[mese] = risparmio_mensile.get(mese, 0) + risparmio
                    
                    descrizione = analisi['spesa']['descrizione'].lower()
                    if any(k in descrizione for k in ['farmacia', 'medico', 'salute']):
                        cat = 'Salute'
                    elif any(k in descrizione for k in ['casa', 'ristruttur']):
                        cat = 'Casa'
                    elif any(k in descrizione for k in ['auto', 'macchina']):
                        cat = 'Auto'
                    elif any(k in descrizione for k in ['figli', 'nido', 'scuola']):
                        cat = 'Famiglia'
                    else:
                        cat = 'Altro'
                    categorie[cat] = categorie.get(cat, 0) + 1
            except:
                continue
        
        media_risparmio = sum(risparmi) / len(risparmi) if risparmi else 0
        return {
            "success": True,
            "totale_analisi": len(cronologia),
            "risparmio_totale": round(risparmio_totale, 2),
            "risparmio_mensile": dict(sorted(risparmio_mensile.items())),
            "categorie": categorie,
            "media_risparmio": round(media_risparmio, 2)
        }
    except Exception as e:
        print(f"❌ Errore statistiche: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ocr-scontrino")
async def ocr_scontrino(request: Request, current_user: dict = Depends(get_current_user)):
    try:
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Nessuna immagine")
        
        base64_image = base64.b64encode(body).decode('utf-8')
        prompt = "Leggi scontrino italiano ed estrai: importo, descrizione, data. Rispondi in JSON."
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ],
            max_tokens=300
        )
        
        try:
            risultato = json.loads(response.choices[0].message.content)
        except:
            import re
            json_match = re.search(r'\{.*?\}', response.choices[0].message.content, re.DOTALL)
            risultato = json.loads(json_match.group()) if json_match else {}
        
        return {"success": True, **risultato}
    except Exception as e:
        print(f"❌ Errore OCR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database_docs": fisco_collection.count()}