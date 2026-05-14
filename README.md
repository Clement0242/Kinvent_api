# kinvent-client

Client Python pour l'[API publique Kinvent](https://api.k-invent.com). Récupère participants, protocoles et métriques calculées — le stockage est laissé à votre charge.

## Installation

```bash
git clone <url-du-repo>
cd kinvent-client
pip install -r requirements.txt
```

## Configuration

Copier `.env.example` en `.env` et renseigner vos identifiants Kinvent :

```bash
cp .env.example .env
```

```ini
KINVENT_USERNAME=votre_email@example.com
KINVENT_PASSWORD=votre_mot_de_passe
KINVENT_API_URL=https://api.k-invent.com
```

## Utilisation

```python
from kinvent import KinventClient

client = KinventClient()  # lit .env automatiquement
client.login()

# Récupérer tous les participants
participants = client.get_participants()

# Récupérer les protocoles (sessions de tests)
protocols = client.get_protocols()

# Sync incrémentale : seulement ce qui a changé depuis un timestamp (ms)
protocols = client.get_protocols(updated_after=1714500000000)

# Calculer les métriques d'une liste de protocoles
codes = [p["code"] for p in protocols[:10]]
results = client.analyze_protocols(codes)
# results["protocolsResults"] contient les métriques par activité
```

## Endpoints disponibles

| Méthode | Description |
|---|---|
| `client.get_participants(updated_after, include_deleted)` | Liste tous les participants |
| `client.get_participant(code)` | Un participant par UUID |
| `client.get_protocols(updated_after, include_deleted)` | Liste tous les protocoles |
| `client.get_protocol(code)` | Un protocole par UUID |
| `client.get_protocols_by_participant(participant_code)` | Protocoles d'un participant |
| `client.analyze_protocols(codes)` | Calcule les métriques (CMJ, RSI, COP...) |
| `client.get_activity_configs()` | Configurations des activités disponibles |

## Types d'exercices

| Code | Description |
|---|---|
| `JUMP_ANALYSIS` | Saut vertical (CMJ, SJ, DJ) — hauteur, RSI, force, puissance... |
| `METER_ENDURANCE` | Force isométrique / endurance — RFD, impulsion... |
| `DYNAMIC_DISTRIBUTION_EVALUATION` | Distribution dynamique (squats, fentes...) |
| `STANDING_EVALUATION` | Équilibre debout / posturographie (COP) |

## Gestion des erreurs

```python
from kinvent import KinventClient
from kinvent.client import KinventAuthError, KinventAPIError

try:
    client = KinventClient()
    client.login()
except KinventAuthError as e:
    print(f"Erreur d'authentification : {e}")
except KinventAPIError as e:
    print(f"Erreur API {e.status_code} : {e}")
```

Le client retry automatiquement x3 avec backoff exponentiel sur les erreurs réseau.
