import { errorResponse, PublicError } from "@/lib/http";
import { requestWorker } from "@/lib/worker";

export const dynamic = "force-dynamic";
export async function GET() {
  try {
    const health = await requestWorker("/health");
    if (!health || typeof health !== "object" || !("status" in health) || health.status !== "ok" || !("mode" in health) || (health.mode !== "live" && health.mode !== "demo") || !("integrations" in health) || !Array.isArray(health.integrations)) {
      throw new PublicError(502, "Worker zwrócił nieprawidłowy stan połączeń.");
    }
    const integrations = health.integrations.map((item: unknown) => {
      if (!item || typeof item !== "object" || !("name" in item) || typeof item.name !== "string" || !("configured" in item) || typeof item.configured !== "boolean" || !("detail" in item) || typeof item.detail !== "string") {
        throw new PublicError(502, "Worker zwrócił nieprawidłowy stan integracji.");
      }
      return { name: item.name, configured: item.configured, detail: item.detail };
    });
    // Expose only the public health contract, never extra configuration fields.
    return Response.json({ status: health.status, mode: health.mode, integrations });
  }
  catch (error) { return errorResponse(error); }
}
