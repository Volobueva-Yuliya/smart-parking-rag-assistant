from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from stage_3.app.config import API_TOKEN

security = HTTPBearer()

def validate_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Simple Bearer token validation helper.
    Compares the provided token with the STAGE_3_API_TOKEN from config.
    """
    if credentials.credentials != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
