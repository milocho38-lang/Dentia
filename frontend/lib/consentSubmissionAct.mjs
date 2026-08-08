import { secureRandomUuid } from "./secureRandomUuid.mjs";

export class ConsentSubmissionAct {
  #completed = false;
  #createKey;
  #inFlight = false;
  #key = "";

  constructor(createKey = secureRandomUuid) {
    this.#createKey = createKey;
  }

  begin() {
    if (this.#completed || this.#inFlight) return null;
    this.#inFlight = true;
    try {
      if (!this.#key) this.#key = this.#createKey();
      return this.#key;
    } catch (error) {
      this.#inFlight = false;
      throw error;
    }
  }

  settle({ completed = false } = {}) {
    this.#inFlight = false;
    if (completed) this.#completed = true;
  }

  invalidate() {
    if (!this.#completed && !this.#inFlight) this.#key = "";
  }
}
