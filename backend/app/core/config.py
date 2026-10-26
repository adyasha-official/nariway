from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "NariWay API"
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Pilot city is configuration, not code, so the project can move cities later.
    # Default is Rourkela, Odisha. Change these three values to move the pilot.
    pilot_city: str = "Rourkela"
    pilot_lat: float = 22.2604
    pilot_lng: float = 84.8536

    # Self-hosted OSRM / Valhalla / GraphHopper-compatible OSRM endpoint, e.g. http://localhost:5000
    # Leave empty to use the clearly-labelled demo routing provider.
    routing_provider_url: str = ""
    # Nominatim-compatible geocoder. The public OSM instance is NOT for production use.
    geocoder_url: str = ""
    geocoder_user_agent: str = "NariWay/0.1 (contact: set-GEOCODER_USER_AGENT)"

    # Never offer a "safer" route slower than this multiple of the fastest candidate.
    max_detour_ratio: float = 1.6

    # SQLite for local dev; set a postgresql:// URL (PostGIS-enabled) for the pilot.
    database_url: str = "sqlite:///./nariway.db"

    # MUST be overridden outside development (startup refuses the default).
    jwt_secret: str = "dev-only-change-me-dev-only-change-me-0000"
    access_token_minutes: int = 60 * 12
    admin_emails: list[str] = []
    public_web_url: str = "http://localhost:5173"

    # Community report policy
    report_ttl_days: int = 90
    reports_per_user_per_day: int = 5
    duplicate_radius_m: float = 50.0
    flags_to_auto_hide: int = 3

    # Journey Guardian
    share_default_hours: int = 6
    overdue_grace_minutes: int = 10


settings = Settings()
