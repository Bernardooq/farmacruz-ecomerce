"""
Token Blacklist — revocación de JWT en memoria.

Almacena JTI → timestamp_expiry de tokens revocados para implementar logout real.
Los JTIs se eliminan automáticamente cuando su token ya habría expirado de todas
formas, por lo que la memoria está acotada al número de tokens activos (no ilimitada).

Como es en memoria, se resetea al reiniciar el servidor (aceptable para una sola
instancia EC2). Para HA multi-instancia, migrar a Redis con TTL.

Uso:
    blacklist.add(jti, exp_timestamp)   # al hacer logout
    blacklist.contains(jti)             # al verificar token
"""

import time
import threading
from typing import Optional

_revoked: dict[str, float] = {}   # jti → unix timestamp de expiración
_lock = threading.Lock()


def _prune() -> None:
    """Elimina JTIs cuyo token ya habría expirado. Llamado internamente en add()."""
    now = time.time()
    expired = [jti for jti, exp in _revoked.items() if exp < now]
    for jti in expired:
        del _revoked[jti]


def add(jti: str, exp: Optional[float] = None) -> None:
    """
    Agrega un JTI a la blacklist.

    Args:
        jti: JWT ID del token a revocar.
        exp: Unix timestamp de expiración del token (del claim 'exp').
             Si no se pasa, se guarda por 24h como margen de seguridad.
    """
    with _lock:
        _prune()  # limpiar expirados antes de agregar
        _revoked[jti] = exp if exp is not None else time.time() + 86400


def contains(jti: str) -> bool:
    """Retorna True si el JTI está revocado Y su token no ha expirado aún."""
    with _lock:
        exp = _revoked.get(jti)
        if exp is None:
            return False
        if exp < time.time():
            # Ya expiró → no hace falta mantenerlo
            del _revoked[jti]
            return False
        return True


def size() -> int:
    """Retorna el número de JTIs actualmente en la blacklist (útil para métricas)."""
    with _lock:
        return len(_revoked)
