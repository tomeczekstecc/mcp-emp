"""Rejestr async HTTP client — fetch_* / create_* / delete_* functions.

All functions obtain the shared httpx.AsyncClient via core.http.get_client()
and the bearer token via core.auth.get_auth().  Implemented incrementally
across M1–M6.
"""
