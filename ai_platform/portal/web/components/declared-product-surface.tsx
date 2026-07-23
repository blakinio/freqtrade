import { dataMode } from "@/lib/portal-api";
import { findProductSurface } from "@/lib/product-surfaces";
import { ProductSurfacePage } from "./product-surface-page";

export function DeclaredProductSurface({ path }: { path: string }) {
  const surface = findProductSurface(path);
  if (!surface) {
    throw new Error(`Unknown declared product surface: ${path}`);
  }
  return <ProductSurfacePage surface={surface} mode={dataMode()} />;
}
