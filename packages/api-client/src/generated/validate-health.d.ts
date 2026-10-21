import type { components } from "./schema";
declare const validate: (data: unknown) => data is components["schemas"]["HealthResponse"];
export default validate;
