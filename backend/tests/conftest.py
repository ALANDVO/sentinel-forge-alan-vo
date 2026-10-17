"""Pytest fixtures for backend tests."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app
from app.services.database import Database


@pytest.fixture
def app():
    """Create a FastAPI app with an in-memory SQLite database."""
    test_app = create_app()
    # Override database with in-memory SQLite for tests
    from sqlalchemy.pool import StaticPool
    from sqlalchemy import create_engine
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_db = Database.__new__(Database)
    test_db._url = "sqlite://"
    test_db._engine = engine
    from sqlalchemy.orm import sessionmaker
    test_db._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    test_app.state.db = test_db
    test_app.state.settings = settings
    return test_app


@pytest.fixture
def client(app):
    """TestClient that runs the lifespan (creating tables)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def demo_settings():
    """Ensure demo mode is active for tests that need it."""
    original = settings.demo_mode
    settings.demo_mode = True
    settings.app_host = "127.0.0.1"
    yield settings
    settings.demo_mode = original


@pytest.fixture
def no_demo_settings():
    """Disable demo mode for auth-rejection tests."""
    original = (settings.demo_mode, settings.api_key)
    settings.demo_mode = False
    settings.api_key = "test-api-key-1234567890"
    yield settings
    settings.demo_mode = original[0]
    settings.api_key = original[1]


# Sample mod source code for testing
SAFE_MOD = '''\
import { defineMod } from '@anthropic-ai/claude-code-mods';

export default defineMod({
  hooks: {
    "ui.press": (ctx) => {
      console.log("Button:", ctx.button);
    },
    "after_command": (ctx) => {
      const summary = ctx.summary;
      console.log("Done:", summary.status);
    },
  },
});
'''

UNSAFE_MOD = '''\
const cp = require('child_process');
const fs = require('fs');

cp.exec('echo hello', (err, stdout) => {
  // no error handling
});

fs.writeFileSync('/tmp/output.txt', 'data');

const res = await fetch('https://api.example.com');
'''

FLICKERING_MOD = '''\
function renderStatus() {
  console.clear();
  console.log("Thinking...");
  process.stdout.cursorTo(0, 0);
  process.stdout.clearScreen();
}
'''

UNBOUNDED_MOD = '''\
let running = true;
while (true) {
  doWork();
}
setInterval(() => {
  checkStatus();
}, 1000);
'''

FETCH_WITH_CATCH = '''\
const response = await fetch('https://api.example.com/data').catch((err) => {
  console.error(err);
});
'''

EMPTY_RESULT_CODE = "const x = 1;"