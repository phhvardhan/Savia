import json
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="savia-tests-")
os.environ.update({
    "DB_PATH": os.path.join(_tmp, "savia.db"),
    "UPLOAD_DIR": _tmp,
    "LLM_PROVIDER": "openai",
    "OPENAI_API_KEY": "",
    "GROQ_API_KEY": "",
    "AZURE_OPENAI_API_KEY": "",
    "AUTH_REQUIRED": "false",
    "SECRET_KEY": "test-secret",
})

import pytest

from app.core.llm import Completion


class FakeLLM:
    def __init__(self):
        self.replies: list = []
        self.calls: list[tuple[str, str]] = []

    def reply(self, *replies):
        self.replies.extend(replies)
        return self

    async def complete(self, system, user, max_tokens=None, json_mode=True):
        self.calls.append((system, user))
        reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        if isinstance(reply, Exception):
            raise reply
        content = reply if isinstance(reply, str) else json.dumps(reply)
        return Completion(content=content, provider="fake", model="fake", finish_reason="stop",
                          prompt_tokens=10, completion_tokens=10)


@pytest.fixture
def fake_llm(monkeypatch):
    fake = FakeLLM()
    monkeypatch.setattr("app.core.llm.complete", fake.complete)
    return fake
