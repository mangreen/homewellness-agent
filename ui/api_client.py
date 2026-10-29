"""HTTP client for the HomeWellness API. The UI talks to the API only through this class."""

import os
import uuid

import httpx

DEMO_ELDER_ID = "demo-elder-001"


class ApiError(Exception):
    """The API answered with an error. It carries the safe fields of the error body."""

    def __init__(self, status: int, code: str, message: str, trace_id: str) -> None:
        super().__init__(f"{status} {code}: {message}")
        self.status, self.code, self.message, self.trace_id = status, code, message, trace_id


class ApiUnavailable(Exception):
    """The API cannot be reached."""


class ApiClient:
    def __init__(self, http: httpx.Client, elder_id: str = DEMO_ELDER_ID) -> None:
        self._http = http
        self._elder = elder_id

    def _call(self, method: str, path: str, **kwargs) -> dict:
        try:
            response = self._http.request(method, path, **kwargs)
        except httpx.HTTPError as error:
            raise ApiUnavailable(type(error).__name__) from error
        if response.status_code >= 400:
            status = response.status_code
            try:
                body = response.json()["error"]
                error = ApiError(status, body["code"], body["message"], body["trace_id"])
            except (ValueError, KeyError, TypeError):
                error = ApiError(status, "http_error", "Unexpected answer.", "-")
            raise error
        return response.json()

    @staticmethod
    def _key() -> dict[str, str]:
        return {"Idempotency-Key": uuid.uuid4().hex}  # A new key for each click.

    def health(self) -> bool:
        try:
            return self._http.get("/healthz").status_code == 200
        except httpx.HTTPError:
            return False

    def send_message(self, text: str) -> str:
        body = self._call("POST", f"/elders/{self._elder}/messages", json={"text": text},
                          headers=self._key())
        return body["reply"]

    def conversation(self, limit: int = 30) -> list[dict]:
        return self._call("GET", f"/elders/{self._elder}/conversation",
                          params={"limit": limit})["turns"]

    def status(self) -> dict:
        return self._call("GET", f"/elders/{self._elder}/status")

    def alerts(self) -> list[dict]:
        return self._call("GET", "/alerts")["alerts"]

    def activity(self, limit: int = 30) -> list[dict]:
        try:
            return self._call("GET", "/demo/activity", params={"limit": limit})["events"]
        except ApiError as error:
            if error.status == 404:  # Not in demo mode.
                return []
            raise

    def start_scenario(self, name: str) -> dict:
        return self._call("POST", f"/sim/scenarios/{name}", headers=self._key())

    def reset(self) -> dict:
        return self._call("POST", "/demo/reset", headers=self._key())


def build_client() -> ApiClient:
    url = os.environ.get("API_URL", "http://localhost:8001")
    return ApiClient(httpx.Client(base_url=url, timeout=10.0))
