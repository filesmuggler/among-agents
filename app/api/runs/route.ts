import { assertSameOrigin, errorResponse, readFixture } from "@/lib/http";
import { requestWorker } from "@/lib/worker";

export async function POST(request: Request) {
  try {
    assertSameOrigin(request);
    const fixture = await readFixture(request);
    return Response.json(await requestWorker("/run", { method: "POST", body: { fixture }, timeoutMs: 600_000 }));
  } catch (error) { return errorResponse(error); }
}
