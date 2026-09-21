export declare function persistAndRefetchDemoRequest<T>(
  action: () => Promise<unknown>,
  refetch: () => Promise<T>,
): Promise<T>;
