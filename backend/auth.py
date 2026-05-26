from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

# Configurações de Segurança (Devem vir de variáveis de ambiente em produção)
SECRET_KEY = "sua_chave_secreta_super_segura_jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Contexto de Criptografia usando bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha em texto plano corresponde à senha criptografada.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # Tratamento de erro seguro
        print(f"Erro ao verificar senha: {e}")
        return False

def get_password_hash(password: str) -> str:
    """
    Gera o hash da senha para armazenamento no banco de dados.
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Cria um token JWT para autenticação.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        print(f"Erro ao gerar token JWT: {e}")
        raise
