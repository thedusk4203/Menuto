import createClient from "openapi-fetch";
import type { components, paths } from "./generated/schema";
import validateHealth from "./generated/validate-health.js";

export type { components, paths } from "./generated/schema";
export type HealthResponse = components["schemas"]["HealthResponse"];

export function createMenutoApi(options: {
  baseUrl?: string;
  fetch?: typeof globalThis.fetch;
} = {}) {
  const client = createClient<paths>({
    baseUrl: options.baseUrl ?? "",
    fetch: options.fetch,
  });
  return {
    client,
    async getHealth(signal?: AbortSignal): Promise<HealthResponse> {
      const { data, error, response } = await client.GET("/api/v1/health", { signal });
      if (!response.ok || error) throw new Error("Không kết nối được dịch vụ Menuto.");
      if (!validateHealth(data)) {
        throw new Error("Phản hồi dịch vụ không khớp hợp đồng OpenAPI hiện tại.");
      }
      return data;
    },
  };
}
