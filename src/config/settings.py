"""
Application Configuration Settings
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # App Configuration
    APP_NAME: str = "Adaptive Command Centre"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # Server Configuration
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    SERVER_WORKERS: int = 4
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/adaptive_cc"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600
    
    # InfluxDB Configuration
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_ORG: str = "adaptive-cc"
    INFLUXDB_BUCKET: str = "metrics"
    INFLUXDB_TOKEN: str = "adaptive-cc-token-1234567890"
    
    # Prometheus Configuration
    PROMETHEUS_URL: str = "http://localhost:9090"
    PROMETHEUS_SCRAPE_INTERVAL: str = "15s"
    
    # Telemetry Thresholds
    JITTER_THRESHOLD_MS: float = 50.0
    PACKET_LOSS_THRESHOLD_PERCENT: float = 1.0
    DELAY_THRESHOLD_MS: float = 100.0
    BUFFER_FILL_THRESHOLD_PERCENT: float = 85.0
    
    # QoS Policy Configuration
    QOS_POLICY_UPDATE_INTERVAL_SEC: int = 60
    QOS_MAX_POLICY_CHANGES_PER_HOUR: int = 60
    QOS_CHANGE_DEBOUNCE_SEC: int = 5  # Prevent rapid successive changes
    
    # Predictive Analytics Configuration
    FORECAST_HORIZON_MIN: int = 30
    FORECAST_WINDOW_MIN: int = 60
    ML_MODEL_PATH: str = "models/forecast_model.pkl"
    ANOMALY_DETECTION_ENABLED: bool = True
    
    # Alert Configuration
    ALERT_RETENTION_DAYS: int = 30
    ALERT_BATCH_SIZE: int = 100
    ALERT_CHECK_INTERVAL_SEC: int = 30
    SLACK_WEBHOOK_URL: Optional[str] = None
    EMAIL_SMTP_SERVER: Optional[str] = None
    EMAIL_SMTP_PORT: int = 587
    EMAIL_FROM_ADDRESS: Optional[str] = None
    
    # SNMP Configuration
    SNMP_COMMUNITY: str = "public"
    SNMP_VERSION: str = "2c"
    SNMP_TIMEOUT: int = 5
    SNMP_RETRIES: int = 3
    SNMP_PORT: int = 161
    
    # SDN Controller Configuration
    SDN_CONTROLLER_URL: str = "http://localhost:8080"
    SDN_CONTROLLER_USER: str = "admin"
    SDN_CONTROLLER_PASSWORD: str = "admin"
    SDN_REQUEST_TIMEOUT: int = 30
    
    # NFV Orchestrator Configuration
    NFV_ORCHESTRATOR_URL: str = "http://localhost:8070"
    NFV_ORCHESTRATOR_USER: str = "admin"
    NFV_ORCHESTRATOR_PASSWORD: str = "admin"
    NFV_REQUEST_TIMEOUT: int = 60
    
    # TR-069 ACS Server Configuration
    ACS_SERVER_URL: str = "http://localhost:7547"
    ACS_USERNAME: str = "admin"
    ACS_PASSWORD: str = "admin"
    ACS_REQUEST_TIMEOUT: int = 30
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_FORMAT: str = "json"
    LOG_MAX_BYTES: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 10
    
    # Security Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Feature Flags
    ENABLE_JITTER_SUPPRESSION: bool = True
    ENABLE_BUFFER_PROTECTION: bool = True
    ENABLE_PREDICTIVE_SCALING: bool = True
    ENABLE_REMOTE_ORCHESTRATION: bool = True
    ENABLE_VIDEO_RECOVERY: bool = True
    
    # Performance Tuning
    TELEMETRY_BATCH_SIZE: int = 100
    TELEMETRY_FLUSH_INTERVAL_SEC: int = 5
    DECISION_ENGINE_INTERVAL_SEC: int = 10
    ANALYTICS_COMPUTE_INTERVAL_SEC: int = 60
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings
