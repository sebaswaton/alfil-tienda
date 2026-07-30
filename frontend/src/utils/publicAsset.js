export function publicAsset(url) {
  if (!url || !url.startsWith("/")) return url;

  // API media URLs are served by the backend and must remain domain-relative.
  if (url.startsWith("/alfil-api/") || url.startsWith("/api/")) return url;

  return `${import.meta.env.BASE_URL}${url.slice(1)}`;
}
