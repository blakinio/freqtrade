import { notFound } from "next/navigation";

import { ProductSurfacePage } from "@/components/product-surface-page";
import { dataMode } from "@/lib/portal-api";
import { findProductSurface } from "@/lib/product-surfaces";

export default async function ProductSurfaceRoute({
  params,
}: {
  params: Promise<{ surface: string[] }>;
}) {
  const { surface } = await params;
  const path = `/${surface.join("/")}`;
  const config = findProductSurface(path);
  if (!config) {
    notFound();
  }
  return <ProductSurfacePage surface={config} mode={dataMode()} />;
}
