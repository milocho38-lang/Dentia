export function Spinner({
  className = "h-5 w-5",
}: {
  className?: string;
}) {
  return (
    <span
      aria-hidden="true"
      className={`dentia-spinner inline-block rounded-full border-2 border-current border-r-transparent ${className}`}
    />
  );
}
