// Pure: caller passes href/ua (or SSR stubs) rather than reading globals.
export function buildErrorReport(
  region: string,
  error: { message: string; stack?: string },
  ctx: { href: string; ua: string },
): string {
  return [
    `${region} error: ${error.message}`,
    "",
    error.stack ?? "(no stack)",
    "",
    `URL: ${ctx.href}`,
    `UA: ${ctx.ua}`,
  ].join("\n");
}
