export type Health = {
  service: "menuto"; status: "ok"; stage: "foundation"; planner_ready: false;
};

export async function getHealth(signal: AbortSignal): Promise<Health> {
  const response = await fetch("/api/v1/health", { signal });
  if (!response.ok) throw new Error("Không kết nối được dịch vụ Menuto.");
  const data: unknown = await response.json();
  if (typeof data !== "object" || data === null ||
      !("service" in data) || data.service !== "menuto" ||
      !("status" in data) || data.status !== "ok" ||
      !("stage" in data) || data.stage !== "foundation" ||
      !("planner_ready" in data) || data.planner_ready !== false) {
    throw new Error("Phản hồi dịch vụ không khớp hợp đồng hiện tại.");
  }
  return data as Health;
}
