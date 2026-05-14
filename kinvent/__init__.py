"""
Package kinvent — client Python pour l'API publique Kinvent.

Usage :
    from kinvent import KinventClient
    client = KinventClient()   # lit .env automatiquement
    client.login()
    participants = client.get_participants()
    protocols = client.get_protocols()
"""

from .client import KinventClient

__all__ = ["KinventClient"]
