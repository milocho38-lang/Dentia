export function resolveClinicalCompletionCatalog(performedItems, catalogProcedure) {
  if (!catalogProcedure) {
    return {
      items: performedItems,
      selectedId: performedItems[0]?.id ?? "",
      error: null,
    };
  }
  const configuredId = catalogProcedure.default_performed_catalog_item_id;
  if (!configuredId) {
    return {
      items: [],
      selectedId: "",
      error: "El procedimiento no tiene un resultado odontográfico realizado configurado.",
    };
  }
  const configured = performedItems.find((item) => item.id === configuredId);
  if (!configured) {
    return {
      items: [],
      selectedId: "",
      error: "El resultado odontográfico configurado no está activo o disponible.",
    };
  }
  return { items: [configured], selectedId: configured.id, error: null };
}
