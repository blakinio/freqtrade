import { NextRequest, NextResponse } from "next/server";

import {
  fixtureIdentityMode,
  isFixtureIdentityState,
  setFixtureIdentity,
} from "@/lib/identity";

export async function POST(request: NextRequest) {
  if (!fixtureIdentityMode()) {
    return NextResponse.json({ detail: "Not found" }, { status: 404 });
  }
  const payload: unknown = await request.json();
  const state =
    typeof payload === "object" && payload !== null
      ? (payload as { state?: unknown }).state
      : undefined;
  if (!isFixtureIdentityState(state)) {
    return NextResponse.json({ detail: "Invalid fixture identity state" }, { status: 422 });
  }
  const response = NextResponse.json(
    { state },
    { headers: { "cache-control": "no-store" } },
  );
  setFixtureIdentity(response, state);
  return response;
}
