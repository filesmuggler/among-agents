import { assertSameOrigin, errorResponse, validRunId } from "@/lib/http";
import { requestWorker } from "@/lib/worker";

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    assertSameOrigin(request);
    const { id } = await context.params;
    return Response.json(await requestWorker(`/runs/${validRunId(id)}/submit`, { method: "POST", timeoutMs: 90_000 }));
  } catch (error) { return errorResponse(error); }
}
