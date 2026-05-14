"""
Client HTTP pour l'API publique Kinvent.

Authentification : Basic Auth (login) -> token X-Auth-Token pour toutes les requetes.
Ref : collection Postman KINVENT Public API v2.1
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()


class KinventAuthError(Exception):
    pass


class KinventAPIError(Exception):
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class KinventClient:
    """Client pour l'API publique Kinvent."""

    def __init__(self, username=None, password=None, base_url=None):
        self.base_url = (base_url or os.getenv("KINVENT_API_URL", "https://api.k-invent.com")).rstrip("/")
        self.username = username or os.getenv("KINVENT_USERNAME")
        self.password = password or os.getenv("KINVENT_PASSWORD")
        self.token = None

        if not self.username or not self.password:
            raise KinventAuthError(
                "KINVENT_USERNAME et KINVENT_PASSWORD doivent etre definis dans .env ou passes en argument."
            )

    # ------------------------------------------------------------------
    # Authentification
    # ------------------------------------------------------------------

    def login(self):
        """Effectue le login et stocke le token d'authentification."""
        url = f"{self.base_url}/api/authorization/login"
        response = requests.post(url, auth=(self.username, self.password))
        if response.status_code != 200:
            raise KinventAuthError(
                f"Echec du login ({response.status_code}): {response.text}"
            )
        data = response.json()
        self.token = data.get("token")
        if not self.token:
            raise KinventAuthError("Aucun token recu lors du login.")
        return data

    def get_account(self):
        """Recupere les infos du compte connecte."""
        return self._get("/api/authorization/self")

    # ------------------------------------------------------------------
    # Participants
    # ------------------------------------------------------------------

    def get_participants(self, updated_after=None, include_deleted=False):
        """
        Recupere tous les participants.

        Args:
            updated_after: timestamp en millisecondes (int) — filtre sur updatedOn
            include_deleted: inclure les participants marques comme supprimes
        """
        params = {}
        if updated_after is not None:
            params["updatedAfter"] = updated_after
        if include_deleted:
            params["includeDeleted"] = "true"
        return self._get("/api/participants/v1", params=params)

    def get_participant(self, code):
        """Recupere un participant par son code UUID."""
        return self._get(f"/api/participants/v1/{code}")

    def get_participants_by_protocol(self, participant_code):
        """Recupere les protocoles lies a un participant."""
        return self._get(
            "/api/protocols/v1/findByParticipantCode",
            params={"participantCode": participant_code},
        )

    # ------------------------------------------------------------------
    # Protocoles (sessions / tests)
    # ------------------------------------------------------------------

    def get_protocols(self, updated_after=None, include_deleted=False):
        """
        Recupere tous les protocoles (sessions de tests).

        Args:
            updated_after: timestamp en millisecondes (int)
            include_deleted: inclure les protocoles supprimes
        """
        params = {}
        if updated_after is not None:
            params["updatedAfter"] = updated_after
        if include_deleted:
            params["includeDeleted"] = "true"
        return self._get("/api/protocols/v1", params=params)

    def get_protocol(self, code):
        """Recupere un protocole par son code UUID."""
        return self._get(f"/api/protocols/v1/{code}")

    def get_protocols_by_participant(self, participant_code):
        """Recupere tous les protocoles d'un participant."""
        return self._get(
            "/api/protocols/v1/findByParticipantCode",
            params={"participantCode": participant_code},
        )

    def get_protocols_by_codes(self, codes):
        """Recupere des protocoles par une liste de codes UUID."""
        return self._post("/api/protocols/v1/findByCodes", json=codes)

    def analyze_protocols(self, codes):
        """Lance l'analyse de protocoles (v2)."""
        return self._post("/api/protocols/v2/analyze", json=codes)

    # ------------------------------------------------------------------
    # Configurations d'activite
    # ------------------------------------------------------------------

    def get_activity_configs(self):
        """Recupere toutes les configurations d'activite."""
        return self._get("/api/activityConfigs/v1")

    def get_activity_config(self, code):
        """Recupere une configuration d'activite par son code."""
        return self._get(f"/api/activityConfigs/v1/{code}")

    # ------------------------------------------------------------------
    # Configurations de tags (Groupes)
    # ------------------------------------------------------------------

    def get_participant_tag_configs(self):
        """Recupere les configurations de tags des participants (Groupes)."""
        return self._get("/api/participantTagConfigs/v1")

    # ------------------------------------------------------------------
    # Methodes HTTP internes
    # ------------------------------------------------------------------

    def _headers(self):
        if not self.token:
            raise KinventAuthError("Non authentifie. Appelez login() d'abord.")
        return {"X-Auth-Token": self.token}

    def _get(self, path, params=None, timeout=120, retries=3):
        url = f"{self.base_url}{path}"
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=self._headers(), params=params, timeout=timeout)
                return self._handle_response(response)
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.ChunkedEncodingError,
                    requests.exceptions.ReadTimeout) as e:
                if attempt == retries - 1:
                    raise
                wait = 2 ** attempt
                time.sleep(wait)

    def _post(self, path, json=None, timeout=120, retries=3):
        url = f"{self.base_url}{path}"
        for attempt in range(retries):
            try:
                response = requests.post(url, headers=self._headers(), json=json, timeout=timeout)
                return self._handle_response(response)
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.ChunkedEncodingError,
                    requests.exceptions.ReadTimeout) as e:
                if attempt == retries - 1:
                    raise
                wait = 2 ** attempt
                time.sleep(wait)

    def _handle_response(self, response):
        if response.status_code in (200, 201):
            return response.json()
        raise KinventAPIError(
            f"Erreur API {response.status_code}: {response.text}",
            status_code=response.status_code,
            response=response,
        )
