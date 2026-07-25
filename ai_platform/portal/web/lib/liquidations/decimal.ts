const DECIMAL_PATTERN = /^(0|[1-9]\d*)(?:\.(\d+))?$/;

interface ParsedDecimal {
  value: bigint;
  scale: number;
}

function parseDecimal(value: string): ParsedDecimal {
  const match = DECIMAL_PATTERN.exec(value);
  if (!match) {
    throw new Error("invalid non-negative decimal string");
  }
  const fraction = match[2] ?? "";
  return {
    value: BigInt(`${match[1]}${fraction}`),
    scale: fraction.length,
  };
}

function formatDecimal(value: bigint, scale: number): string {
  if (scale === 0) {
    return value.toString();
  }
  const padded = value.toString().padStart(scale + 1, "0");
  const whole = padded.slice(0, -scale);
  const fraction = padded.slice(-scale).replace(/0+$/, "");
  return fraction ? `${whole}.${fraction}` : whole;
}

export function normalizeDecimal(value: string): string {
  const parsed = parseDecimal(value);
  return formatDecimal(parsed.value, parsed.scale);
}

export function addDecimalStrings(left: string, right: string): string {
  const leftParsed = parseDecimal(left);
  const rightParsed = parseDecimal(right);
  const scale = Math.max(leftParsed.scale, rightParsed.scale);
  const leftValue = leftParsed.value * 10n ** BigInt(scale - leftParsed.scale);
  const rightValue = rightParsed.value * 10n ** BigInt(scale - rightParsed.scale);
  return formatDecimal(leftValue + rightValue, scale);
}

export function sumDecimalStrings(values: Iterable<string>): string {
  let total = "0";
  for (const value of values) {
    total = addDecimalStrings(total, value);
  }
  return total;
}
