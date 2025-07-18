import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file

GOLEMIO_API_KEY = os.getenv("GOLEMIO_API_KEY")
NOMINATIM_URL = os.getenv("NOMINATIM_URL", "http://nominatim:8080")
OTP_URL = os.getenv("OTP_URL", "http://otp:8080/otp/transmodel/v3")
STOPS_FILE = os.getenv("STOPS_FILE")
NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN")
