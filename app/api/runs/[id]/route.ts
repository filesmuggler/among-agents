import { errorResponse, validRunId } from "@/lib/http";
import { requestWorker } from "@/lib/worker";

export const dynamic = "force-dynamic";
export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await context.params;
    return Response.json(await requestWorker(`/runs/${validRunId(id)}`));
  } catch (error) { return errorResponse(error); }
}
