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
      ? { revoked: true }
      : await forwardControlPlaneMutation<{ revoked: boolean }>(
          request,
          "/v1/identity/logout",
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
      NextResponse.json({ detail: "Portal logout failed" }, { status: 502 })
    );
  }
}
