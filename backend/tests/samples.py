"""Sample mod source code for tests."""
from __future__ import annotations

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

MINIMAL_CODE = "const x = 1;"

LONG_CODE = "x" * 100_001