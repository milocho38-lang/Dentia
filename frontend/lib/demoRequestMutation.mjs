export async function persistAndRefetchDemoRequest(action, refetch) {
  await action();
  return refetch();
}
