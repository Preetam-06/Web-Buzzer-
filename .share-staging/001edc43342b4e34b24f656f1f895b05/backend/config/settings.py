from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"  # plain for MVP, hashed check via bcrypt optional
    REDIS_URL: str = "redis://localhost:6379/0"
    DATA_DIR: str = "data"
    CORS_ORIGINS: list = ["*"]
    HOST_LAN_IP: str = ""  # Set via env for Docker: real host LAN IP (e.g., 192.168.1.10) so QR uses host IP not container IP

    class Config:
        env_file = ".env"

settings = Settings()
