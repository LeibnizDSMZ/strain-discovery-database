from pathlib import Path
from saim.taxon_name.private.container import LPSNConf
import os


def create_lpsn_config() -> LPSNConf:

    user = os.getenv("LPSN_USER")
    password_file = os.getenv("LPSN_PASSWORD_FILE")

    if not user:
        raise ValueError("Environment variable LPSN_USER is not set")
    if password_file:
        try:
            with Path(password_file).open("r") as fhd:
                pw = fhd.read().strip()
        except IOError as exc:
            raise ValueError(f"Failed to read password file: {exc}")
    elif not (pw := os.getenv("LPSN_PASSWORD")):
        raise ValueError("LPSN_PASSWORD is not set")

    return LPSNConf(user=user, pw=pw, url="https://sso.dsmz.de/auth/")
