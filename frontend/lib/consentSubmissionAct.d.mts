export class ConsentSubmissionAct {
  constructor(createKey?: () => string);
  begin(): string | null;
  settle(options?: { completed?: boolean }): void;
  invalidate(): void;
}
