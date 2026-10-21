import { createMenutoApi } from "@menuto/api-client";
export type { HealthResponse as Health } from "@menuto/api-client";

const api = createMenutoApi();
export const getHealth = api.getHealth;
