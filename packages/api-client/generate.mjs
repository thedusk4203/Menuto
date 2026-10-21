import { readFile, writeFile, mkdir } from "node:fs/promises";
import openapiTS, { astToString } from "openapi-typescript";
import Ajv2020 from "ajv/dist/2020.js";
import standaloneCode from "ajv/dist/standalone/index.js";

const source = new URL("../contracts/openapi.json", import.meta.url);
const target = new URL("./src/generated/", import.meta.url);
const document = JSON.parse(await readFile(source, "utf8"));
if (!document.openapi?.startsWith("3.1")) {
  throw new Error("Runtime schema generation currently supports OpenAPI 3.1 JSON Schema only.");
}
function auditReferences(value) {
  if (Array.isArray(value)) return value.forEach(auditReferences);
  if (!value || typeof value !== "object") return;
  for (const [key, entry] of Object.entries(value)) {
    if (key === "$ref" && (typeof entry !== "string" || !entry.startsWith("#/components/"))) {
      throw new Error("Only in-document component references are permitted.");
    }
    auditReferences(entry);
  }
}
auditReferences(document);
// Generation is local-only: never resolve arbitrary remote references from a spec.
function rewrite(value) {
  if (Array.isArray(value)) return value.map(rewrite);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, entry]) => {
      if (key === "$ref") {
        if (!entry.startsWith("#/components/schemas/")) {
          throw new Error("Only local component-schema references are allowed: " + entry);
        }
        return [key, entry.replace("#/components/schemas/", "#/$defs/")];
      }
      return [key, rewrite(entry)];
    }));
  }
  return value;
}
const runtime = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "urn:menuto:api-schemas",
  $defs: rewrite(document.components?.schemas ?? {}),
};
const healthRef = document.paths["/api/v1/health"].get.responses["200"]
  .content["application/json"].schema.$ref;
if (!healthRef?.startsWith("#/components/schemas/")) {
  throw new Error("Health response must reference a local component schema.");
}
const healthName = healthRef.slice("#/components/schemas/".length);
if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(healthName)) {
  throw new Error("Unsupported generated response type identifier.");
}
const ajv = new Ajv2020({
  allErrors: true, strict: false, code: { source: true, esm: true },
});
ajv.addSchema(runtime);
const validate = ajv.compile({
  $ref: "urn:menuto:api-schemas#/$defs/" + healthName,
});
const generated = {
  "schema.d.ts": "// Generated from packages/contracts/openapi.json. Do not edit.\n"
    + astToString(await openapiTS(document)),
  "runtime-schemas.json": JSON.stringify(runtime, null, 2) + "\n",
  "validate-health.js": "// Generated from OpenAPI. No runtime schema compiler.\n"
    + standaloneCode(ajv, validate) + "\n",
  "validate-health.d.ts": 'import type { components } from "./schema";\n'
    + 'declare const validate: (data: unknown) => data is components["schemas"]["'
    + healthName + '"];\nexport default validate;\n',
};
const check = process.argv.includes("--check");
if (!check) await mkdir(target, { recursive: true });
for (const [name, content] of Object.entries(generated)) {
  const path = new URL(name, target);
  if (check) {
    let existing;
    try { existing = await readFile(path, "utf8"); } catch { existing = undefined; }
    if (existing?.replaceAll("\r\n", "\n") !== content.replaceAll("\r\n", "\n")) {
      throw new Error("Generated contract drift: " + name + "; run npm run contracts:generate");
    }
  } else {
    await writeFile(path, content, "utf8");
  }
}
console.log(check ? "Generated API contracts match OpenAPI." : "API types and runtime schemas generated.");
