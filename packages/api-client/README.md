# API client

Private TypeScript workspace package consumed by web. HTTP path/request/response types are generated from packages/contracts/openapi.json with pinned openapi-typescript; openapi-fetch supplies the typed transport. AJV compiles standalone runtime validators during generation from the same OpenAPI 3.1 component schemas, never handwritten field contracts. The browser ships no runtime schema compiler or eval requirement.

From repository root:

- `npm ci`
- `npm run contracts:generate` after exporting OpenAPI from FastAPI.
- `npm run contracts:check` to fail on generated drift.
- `npm run typecheck:client`, `npm run test:client`, `npm run build:web`.

Consumers import `createMenutoApi` or generated `paths/components`. The health convenience method uses the generated response schema for runtime validation; future operations must use generated contracts too.

The generator accepts local component references only. It does not install packages or read secrets from spec content. This is a foundation client, not a promise of implemented business endpoints or native mobile apps.

The generator/client toolchain pins TypeScript 5.9.3 to match the generator peer contract; the web compiler remains pinned separately.
