export const PRIVATE_NO_STORE_CACHE_CONTROL = "private, no-store";

export type HeaderBearingResponse = {
  headers: Headers;
};

export type ResponseHeader = {
  key: string;
  value: string;
};

export function privateNoStoreResponseHeaders(): ResponseHeader[] {
  return [{ key: "Cache-Control", value: PRIVATE_NO_STORE_CACHE_CONTROL }];
}

export function applyPrivateNoStoreCachePolicy<T extends HeaderBearingResponse>(response: T): T {
  response.headers.set("cache-control", PRIVATE_NO_STORE_CACHE_CONTROL);
  return response;
}
