import os
import secrets

import requests
from dotenv import load_dotenv

load_dotenv()

# Provedor do código por SMS: "twilio" (Twilio Verify) ou "textbee"
SMS_PROVIDER = os.getenv("SMS_PROVIDER", "twilio").lower()
# Em desenvolvimento o código só aparece no log, sem gastar SMS nem verificações do Twilio
SMS_DEV_MODE = os.getenv("SMS_DEV_MODE", "false").lower() == "true"

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_VERIFY_SERVICE_SID = os.getenv("TWILIO_VERIFY_SERVICE_SID")

TEXTBEE_URL = "https://api.textbee.dev/api/v1/gateway/send-sms"
TEXTBEE_API_KEY = os.getenv("TEXTBEE_API_KEY")


class SMSError(Exception):
    pass


def _post(url: str, **kwargs) -> requests.Response:
    try:
        return requests.post(url, timeout=10, **kwargs)
    except requests.RequestException as error:
        raise SMSError(f"Falha ao falar com o provedor de SMS: {error}") from error


# ---------- Twilio Verify: o Twilio gera, envia e confere o código ----------
def _twilio_verify(path: str, data: dict) -> requests.Response:
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_VERIFY_SERVICE_SID):
        raise SMSError("TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN ou TWILIO_VERIFY_SERVICE_SID não definidos")
    # A API do Twilio autentica com HTTP Basic (Account SID + Auth Token)
    return _post(
        f"https://verify.twilio.com/v2/Services/{TWILIO_VERIFY_SERVICE_SID}/{path}",
        auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
        data=data,
    )


def _twilio_start(phone: str):
    response = _twilio_verify("Verifications", {"To": phone, "Channel": "sms", "Locale": "pt-BR"})
    if not response.ok:
        raise SMSError(f"Twilio recusou o envio ({response.status_code}): {response.text}")


def _twilio_check(phone: str, code: str) -> bool:
    response = _twilio_verify("VerificationCheck", {"To": phone, "Code": code})
    if response.status_code in (404, 429):
        return False  # verificação expirada, já usada ou com tentativas esgotadas no Twilio
    if not response.ok:
        raise SMSError(f"Twilio recusou a conferência ({response.status_code}): {response.text}")
    return response.json().get("status") == "approved"


# ---------- textbee: a API gera o código e o textbee só envia o SMS ----------
def _textbee_send(phone: str, message: str):
    if not TEXTBEE_API_KEY:
        raise SMSError("TEXTBEE_API_KEY não definida")
    response = _post(
        TEXTBEE_URL,
        headers={"x-api-key": TEXTBEE_API_KEY},
        json={"recipients": [phone], "message": message},
    )
    if not response.ok:
        raise SMSError(f"textbee recusou o SMS ({response.status_code}): {response.text}")


# ---------- Interface usada pelo login ----------
def uses_twilio_verify() -> bool:
    return SMS_PROVIDER == "twilio" and not SMS_DEV_MODE


def send_code(phone: str) -> str | None:
    """Envia o código para o telefone.

    Retorna o código gerado pela API (para ser guardado em hash) ou None quando
    quem gera e confere o código é o Twilio Verify.
    """
    if uses_twilio_verify():
        _twilio_start(phone)
        return None

    code = f"{secrets.randbelow(10**6):06d}"
    message = f"Seu código de acesso à Wishlist: {code}. Válido por 5 minutos."
    if SMS_DEV_MODE:
        print(f"[SMS_DEV_MODE] para {phone}: {message}", flush=True)
    elif SMS_PROVIDER == "textbee":
        _textbee_send(phone, message)
    else:
        raise SMSError(f"SMS_PROVIDER inválido: {SMS_PROVIDER}")
    return code


def check_code(phone: str, code: str) -> bool:
    """Confere o código no Twilio Verify (só usado quando send_code retornou None)."""
    return _twilio_check(phone, code)
