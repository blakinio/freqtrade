import { NextRequest, NextResponse } from "next/server";

import {
  clearIdentityCookies,
  fixtureIdentityMode,
  forwardControlPlaneMutation,
  identityErrorResponse,
  requireBrowserMutation,
} from "@/lib/identity";

export async function POST(request: NextRequest) {
  try {
    requireBrowserMutation(request);
    const payload = fixtureIdentityMode()
      ? { revoked_sessions: 2 }
      : await forwardControlPlaneMutation<{ revoked_sessions: number }>(
          request,
          "/v1/identity/logout-all",
          "POST",
        );
    const response = NextResponse.json(payload, {
      headers: { "cache-control": "no-store" },
    });
    clearIdentityCookies(response);
    return response;
  } catch (error) {
    return (
      identityErrorResponse(error) ??
      NextResponse.json({ detail: "Portal logout-all failed" }, { status: 502 })
    );
  }
}
