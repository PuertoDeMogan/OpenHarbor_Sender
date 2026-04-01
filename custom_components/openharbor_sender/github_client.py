from __future__ import annotations

import base64
import json
import logging
from .const import (
    DATA_REPO_OWNER,
    DATA_REPO_NAME,
)
import aiohttp

_LOGGER = logging.getLogger(__name__)

API_BASE = f"https://api.github.com/repos/{DATA_REPO_OWNER}/{DATA_REPO_NAME}/contents/ports"
RAW_BASE = f"https://raw.githubusercontent.com/{DATA_REPO_OWNER}/{DATA_REPO_NAME}/refs/heads/main/ports"


class GitHubClient:
    def __init__(self, token: str, session: aiohttp.ClientSession) -> None:
        self._token = token
        self._session = session
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def validate_token(self) -> None:
        repo_url = f"https://api.github.com/repos/{DATA_REPO_OWNER}/{DATA_REPO_NAME}"
        try:
            async with self._session.get(
                repo_url,
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 401:
                    _LOGGER.error("validate_token: token inválido (401)")
                    raise ValueError("invalid_token")
                if resp.status == 404:
                    _LOGGER.error("validate_token: repo no encontrado (404)")
                    raise ValueError("repo_not_found")
                resp.raise_for_status()
                data = await resp.json()
                if not data.get("permissions", {}).get("push", False):
                    _LOGGER.error("validate_token: el token no tiene permisos de escritura")
                    raise ValueError("token_no_write")
        except aiohttp.ClientConnectorError as err:
            raise ValueError("cannot_connect") from err

    async def get_port_data(self, port_id: str) -> dict:
        url = f"{RAW_BASE}/{port_id}.json"
        try:
            async with self._session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 404:
                    raise ValueError("port_not_found")
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except aiohttp.ClientConnectorError as err:
            raise ValueError("cannot_connect") from err

    async def put_port_data(self, port_id: str, payload: dict) -> None:
        url = f"{API_BASE}/{port_id}.json"
        sha = await self._get_file_sha(port_id)

        content = base64.b64encode(
            json.dumps(payload, ensure_ascii=False, indent=2).encode()
        ).decode()

        body = {
            "message": f"update: {port_id} sensor data",
            "content": content,
            "branch": "main",
        }
        if sha:
            body["sha"] = sha

        try:
            async with self._session.put(
                url,
                headers=self._headers,
                json=body,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status not in (200, 201):
                    text = await resp.text()
                    raise RuntimeError(f"GitHub PUT failed {resp.status}: {text}")
        except aiohttp.ClientConnectorError:
            raise

    async def _get_file_sha(self, port_id: str) -> str | None:
        url = f"{API_BASE}/{port_id}.json"
        try:
            async with self._session.get(
                url,
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 404:
                    return None
                resp.raise_for_status()
                data = await resp.json()
                return data.get("sha")
        except aiohttp.ClientConnectorError:
            raise
