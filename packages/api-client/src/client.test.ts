import { describe, expect, it, vi } from "vitest";
import { createMenutoApi } from "./index";

const healthy = { service: "menuto", status: "ok", stage: "foundation", planner_ready: false };

function stub(body: unknown, status = 200) {
  return vi.fn<typeof globalThis.fetch>().mockResolvedValue(new Response(
    JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } },
  ));
}

describe("OpenAPI-derived client", () => {
  it("requests the declared endpoint and returns its validated response", async () => {
    const fetch = stub(healthy);
    const api = createMenutoApi({ baseUrl: "https://menuto.test", fetch });
    await expect(api.getHealth()).resolves.toEqual(healthy);
    const request = fetch.mock.calls[0][0] as Request;
    expect(request.url).toBe("https://menuto.test/api/v1/health");
    expect(request.method).toBe("GET");
  });

  it.each([
    {},
    { ...healthy, planner_ready: true },
    { ...healthy, status: "broken" },
    { ...healthy, service: "other" },
    null,
    "not-an-object",
  ])("rejects a response that violates generated runtime schemas: %j", async (body) => {
    const api = createMenutoApi({ baseUrl: "https://menuto.test", fetch: stub(body) });
    await expect(api.getHealth()).rejects.toThrow("OpenAPI");
  });

  it("rejects HTTP errors even with a plausible response body", async () => {
    const api = createMenutoApi({ baseUrl: "https://menuto.test", fetch: stub(healthy, 503) });
    await expect(api.getHealth()).rejects.toThrow("Không kết nối");
  });

  it("propagates network failures", async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockRejectedValue(new Error("offline"));
    const api = createMenutoApi({ baseUrl: "https://menuto.test", fetch });
    await expect(api.getHealth()).rejects.toThrow("offline");
  });

  it("preserves cancellation at the request boundary", async () => {
    const fetch = stub(healthy);
    const controller = new AbortController();
    const api = createMenutoApi({ baseUrl: "https://menuto.test", fetch });
    await api.getHealth(controller.signal);
    controller.abort();
    const request = fetch.mock.calls[0][0] as Request;
    expect(request.signal.aborted).toBe(true);
  });
});
