import type { MetadataRoute } from "next";
import { siteUrl } from "@/lib/site";

const routes = ["", "/producto", "/precios", "/seguridad", "/demo", "/privacidad", "/terminos"];

export default function sitemap(): MetadataRoute.Sitemap {
  return routes.map((route) => ({
    url: `${siteUrl}${route}`,
    lastModified: new Date(),
    changeFrequency: route === "" ? "weekly" : "monthly",
    priority: route === "" ? 1 : 0.7,
  }));
}
