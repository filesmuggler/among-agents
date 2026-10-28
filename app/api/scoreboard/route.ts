import { errorResponse } from "@/lib/http";
import { requestWorker } from "@/lib/worker";

export const dynamic = "force-dynamic";
export async function GET() {
  try { return Response.json(await requestWorker("/scoreboard", { timeoutMs: 30_000 })); }
  catch (error) { return errorResponse(error); }
}
