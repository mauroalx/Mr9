export type InventoryFilters = {
  q: string;
  status: "all" | "online" | "offline";
  manufacturer: string;
  model: string;
  firmware: string;
  tag: string;
};

export function buildInventorySearchParams(
  filters: InventoryFilters,
  page: number,
  queryOverride?: string,
) {
  const params = new URLSearchParams({
    limit: "10",
    skip: String(page * 10),
  });
  const query = (queryOverride ?? filters.q).trim();
  if (query) params.set("q", query);
  if (filters.status !== "all") {
    params.set("online", String(filters.status === "online"));
  }
  for (const [name, value] of [
    ["manufacturer", filters.manufacturer],
    ["model", filters.model],
    ["firmware", filters.firmware],
    ["tag", filters.tag],
  ] as const) {
    if (value !== "all") params.set(name, value);
  }
  return params;
}
