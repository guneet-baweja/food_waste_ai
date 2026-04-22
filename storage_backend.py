import json
import mimetypes
import os
import uuid
from datetime import datetime, timezone
from urllib import error, parse, request


STATE_KEY_MAP = {
    "users.json": "users",
    "donations.json": "donations",
    "notifications.json": "notifications",
    "leaderboard.json": "leaderboard",
    "insurance.json": "insurance",
    "futures_market.json": "futures_market",
    "carbon_credits.json": "carbon_credits",
}


class SupabaseStorageBackend:
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        self.key = (
            os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            or os.environ.get("SUPABASE_KEY")
            or os.environ.get("SUPABASE_ANON_KEY")
            or ""
        )
        self.bucket = os.environ.get("SUPABASE_STORAGE_BUCKET", "food-images")

    @property
    def configured(self):
        return bool(self.url and self.key)

    def state_key_for_file(self, filepath):
        return STATE_KEY_MAP.get(os.path.basename(filepath))

    def _request(self, method, path, payload=None, headers=None, content_type="application/json"):
        if not self.configured:
            raise RuntimeError("Supabase is not configured")

        url = f"{self.url}{path}"
        body = None
        final_headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
        }
        if headers:
            final_headers.update(headers)

        if payload is not None:
            if content_type == "application/json":
                body = json.dumps(payload).encode("utf-8")
            else:
                body = payload
            final_headers["Content-Type"] = content_type

        req = request.Request(url, data=body, headers=final_headers, method=method)
        try:
            with request.urlopen(req, timeout=20) as response:
                raw = response.read()
                if not raw:
                    return None
                if "application/json" in response.headers.get("Content-Type", ""):
                    return json.loads(raw.decode("utf-8"))
                return raw
        except error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Supabase request failed ({exc.code}): {message}") from exc

    def load_state(self, state_key, default_value):
        escaped_key = parse.quote(state_key, safe="")
        data = self._request(
            "GET",
            f"/rest/v1/app_state?key=eq.{escaped_key}&select=payload",
            headers={"Accept": "application/json"},
        )
        if not data:
            return default_value
        return data[0].get("payload", default_value)

    def save_state(self, state_key, payload):
        row = {
            "key": state_key,
            "payload": payload,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._request(
            "POST",
            "/rest/v1/app_state",
            payload=[row],
            headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
        )

    def upload_image(self, file_bytes, filename, content_type=None):
        safe_name = os.path.basename(filename).replace(" ", "-")
        object_path = f"uploads/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/{uuid.uuid4()}-{safe_name}"
        encoded_path = parse.quote(f"{self.bucket}/{object_path}", safe="/")
        mime = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        self._request(
            "POST",
            f"/storage/v1/object/{encoded_path}",
            payload=file_bytes,
            headers={"x-upsert": "true"},
            content_type=mime,
        )
        return f"{self.url}/storage/v1/object/public/{self.bucket}/{object_path}"


supabase_backend = SupabaseStorageBackend()
