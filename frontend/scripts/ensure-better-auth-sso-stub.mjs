// @better-auth/infra dynamically imports @better-auth/sso, but the package
// has broken internal dependencies. We provide a minimal stub so the build
// doesn't fail on the optional SSO module.
import { existsSync, mkdirSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const stubDir = join(__dirname, "..", "node_modules", "@better-auth", "sso");
const stubFile = join(stubDir, "dist", "index.mjs");
const pkgFile = join(stubDir, "package.json");

if (!existsSync(stubFile)) {
  mkdirSync(join(stubDir, "dist"), { recursive: true });
  writeFileSync(stubFile, "// Empty stub – @better-auth/sso is optional; see ensure-better-auth-sso-stub.mjs\nexport {};\n");
  writeFileSync(
    pkgFile,
    JSON.stringify({ name: "@better-auth/sso", version: "0.0.0-stub", private: true, main: "dist/index.mjs", module: "dist/index.mjs", type: "module" }),
  );
  console.log("Created @better-auth/sso stub in node_modules.");
}
