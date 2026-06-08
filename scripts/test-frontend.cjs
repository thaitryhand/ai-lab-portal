#!/usr/bin/env node
// Cross-platform test runner for frontend node:test files.
// Finds all *.test.ts files under frontend/ (excluding node_modules)
// and passes them to tsx --test.

const { spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const frontendDir = path.resolve(__dirname, "..", "frontend");

function findTestFiles(dir) {
  const results = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules") continue;
      if (entry.name.startsWith(".")) continue;
      results.push(...findTestFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith(".test.ts")) {
      results.push(fullPath);
    }
  }
  return results;
}

const testFiles = findTestFiles(frontendDir);
if (testFiles.length === 0) {
  console.error("No test files found.");
  process.exit(1);
}

// Use relative paths from frontend/ so tsx resolves module imports correctly
const relativePaths = testFiles.map((f) => path.relative(frontendDir, f));

const result = spawnSync(
  "npx",
  ["tsx", "--test", ...relativePaths],
  {
    cwd: frontendDir,
    stdio: "inherit",
    shell: true,
  },
);

process.exit(result.status ?? 1);
