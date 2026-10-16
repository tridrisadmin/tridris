// One action tool in TypeScript (Node 18+, no packages): ask Tridris, and wait if a person needs to approve.
//   TRIDRIS_URL=... TRIDRIS_AGENT_TOKEN=... npx tsx refund-tool.ts <order ID> <amount in cents>

const base = process.env.TRIDRIS_URL!.replace(/\/+$/, '');
const headers = { authorization: `Bearer ${process.env.TRIDRIS_AGENT_TOKEN}`, 'content-type': 'application/json' };

interface ActionResult {
  action_id: string;
  status: 'executed' | 'held' | 'denied' | 'approved' | 'rejected' | 'expired' | 'executing' | 'failed';
  message: string;
  reasons: string[];
}

export async function issueRefund(orderId: string, amountCents: number, reason: string, runId: string, ticketId: string): Promise<ActionResult> {
  const res = await fetch(`${base}/v1/actions`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      type: 'refund',
      params: { orderId, amountCents, reason },
      run_id: runId, // groups every action from one conversation or task
      idempotency_key: `refund-${ticketId}`, // reuse it when you retry: nothing runs twice
    }),
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.message ?? `Tridris returned ${res.status}`); // 503: nothing ran, try again shortly
  return body as ActionResult;
}

/** Polls a held action until a person decides or it expires. */
export async function waitForDecision(actionId: string, timeoutMs = 15 * 60_000): Promise<ActionResult> {
  const until = Date.now() + timeoutMs;
  for (;;) {
    const result = (await (await fetch(`${base}/v1/actions/${actionId}`, { headers })).json()) as ActionResult;
    if (!['held', 'approved', 'executing'].includes(result.status) || Date.now() > until) return result;
    await new Promise((r) => setTimeout(r, 3_000));
  }
}

async function main(): Promise<void> {
  const [orderId, amount] = process.argv.slice(2);
  if (!orderId || !amount) return;
  const first = await issueRefund(orderId, Number(amount), 'Arrived damaged', 'example-run', `ticket-${Date.now()}`);
  console.log(first.status, '-', first.message);
  if (first.status === 'held') {
    console.log('Waiting for a decision. Approve or reject it in your developer view…');
    const final = await waitForDecision(first.action_id);
    console.log(final.status, '-', final.message);
  }
}

void main();
