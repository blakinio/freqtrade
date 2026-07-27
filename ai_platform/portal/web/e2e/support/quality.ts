import { expect, type Page, type TestInfo } from "@playwright/test";

const sensitiveValue = /(authorization|cookie|password|secret|token|api[_-]?key)(\s*[:=]\s*)([^\s,;]+)/gi;

export function redactEvidence(value: string): string {
  return value.replace(sensitiveValue, "$1$2[REDACTED]");
}

export async function attachFailureEvidence(
  testInfo: TestInfo,
  consoleMessages: string[],
  failedRequests: string[],
): Promise<void> {
  if (testInfo.status === testInfo.expectedStatus) {
    return;
  }

  await testInfo.attach("browser-console.txt", {
    body: Buffer.from(consoleMessages.map(redactEvidence).join("\n") || "No console messages"),
    contentType: "text/plain",
  });
  await testInfo.attach("failed-requests.txt", {
    body: Buffer.from(failedRequests.map(redactEvidence).join("\n") || "No failed requests"),
    contentType: "text/plain",
  });
}

export async function expectNoUnclippedHorizontalOverflow(page: Page): Promise<void> {
  const overflowSources = await page.evaluate(() => {
    const viewportWidth = window.innerWidth;
    return [...document.querySelectorAll<HTMLElement>("body *")]
      .map((element) => {
        const bounds = element.getBoundingClientRect();
        let parent = element.parentElement;
        let clipped = false;
        while (parent) {
          const overflowX = getComputedStyle(parent).overflowX;
          if (["auto", "scroll", "hidden", "clip"].includes(overflowX)) {
            clipped = true;
            break;
          }
          parent = parent.parentElement;
        }
        return {
          tag: element.tagName.toLowerCase(),
          className: String(element.className),
          right: Math.round(bounds.right),
          width: Math.round(bounds.width),
          clipped,
        };
      })
      .filter((item) => !item.clipped && item.right > viewportWidth + 1)
      .sort((left, right) => right.right - left.right)
      .slice(0, 10);
  });

  expect(overflowSources, `Unclipped horizontal overflow: ${JSON.stringify(overflowSources)}`).toEqual(
    [],
  );
}

export async function expectBaselineAccessibility(page: Page): Promise<void> {
  const violations = await page.evaluate(() => {
    const findings: string[] = [];
    const ids = new Map<string, number>();

    document.querySelectorAll<HTMLElement>("[id]").forEach((element) => {
      ids.set(element.id, (ids.get(element.id) ?? 0) + 1);
    });
    ids.forEach((count, id) => {
      if (count > 1) findings.push(`duplicate-id:${id}`);
    });

    document.querySelectorAll<HTMLImageElement>("img").forEach((image, index) => {
      if (!image.hasAttribute("alt")) findings.push(`image-without-alt:${index}`);
    });

    document.querySelectorAll<HTMLElement>("button, input, select, textarea, a[href]").forEach(
      (element, index) => {
        const labelled =
          element.getAttribute("aria-label") ||
          element.getAttribute("aria-labelledby") ||
          element.textContent?.trim() ||
          (element instanceof HTMLInputElement && element.labels?.length);
        if (!labelled) findings.push(`unlabelled-control:${element.tagName.toLowerCase()}:${index}`);
      },
    );

    if (!document.querySelector("main")) findings.push("missing-main-landmark");
    if (!document.title.trim()) findings.push("missing-document-title");

    return findings;
  });

  expect(violations, `Baseline accessibility violations: ${violations.join(", ")}`).toEqual([]);
}
