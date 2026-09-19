import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import {
  AUTOPLAY_DELAY_MS,
  MANUAL_INTERACTION_PAUSE_MS,
  getNextCarouselSlideIndex,
  shouldRunCarouselAutoplay,
} from "../lib/carouselAutoplay.ts";

const runningState = {
  reducedMotion: false,
  userPaused: false,
  interactionPaused: false,
  hoverPaused: false,
  focusPaused: false,
  pageVisible: true,
  inViewport: true,
};

assert.equal(AUTOPLAY_DELAY_MS, 6000);
assert.ok(MANUAL_INTERACTION_PAUSE_MS >= 8000 && MANUAL_INTERACTION_PAUSE_MS <= 12000);
assert.equal(shouldRunCarouselAutoplay(runningState), true, "Autoplay starts with no-preference");
assert.equal(getNextCarouselSlideIndex(0, 8), 1, "Autoplay advances to the next slide");
assert.equal(getNextCarouselSlideIndex(7, 8), 0, "Autoplay loops from the last slide to the first");

assert.equal(shouldRunCarouselAutoplay({ ...runningState, hoverPaused: true }), false, "Hover pauses autoplay");
assert.equal(shouldRunCarouselAutoplay({ ...runningState, hoverPaused: false }), true, "Mouseleave resumes autoplay");
assert.equal(shouldRunCarouselAutoplay({ ...runningState, focusPaused: true }), false, "Keyboard focus pauses autoplay");
assert.equal(shouldRunCarouselAutoplay({ ...runningState, focusPaused: false }), true, "Focusout resumes autoplay");
assert.equal(shouldRunCarouselAutoplay({ ...runningState, interactionPaused: true }), false, "Manual interaction pauses autoplay");
assert.equal(shouldRunCarouselAutoplay({ ...runningState, interactionPaused: false }), true, "Autoplay resumes after manual interaction");
assert.equal(shouldRunCarouselAutoplay({ ...runningState, reducedMotion: true }), false, "Reduced motion disables autoplay");
assert.equal(shouldRunCarouselAutoplay({ ...runningState, pageVisible: false }), false, "Hidden documents pause autoplay");
assert.equal(shouldRunCarouselAutoplay({ ...runningState, pageVisible: true }), true, "Visible documents resume autoplay");
assert.equal(shouldRunCarouselAutoplay({ ...runningState, inViewport: false }), false, "Offscreen carousel pauses autoplay");
assert.equal(shouldRunCarouselAutoplay({ ...runningState, userPaused: true }), false, "Explicit pause remains respected");

const component = readFileSync(resolve(import.meta.dirname, "../components/ProductCarousel.tsx"), "utf8");
assert.match(component, /window\.setTimeout\([\s\S]*MANUAL_INTERACTION_PAUSE_MS/);
assert.match(component, /window\.clearTimeout\(interactionResumeTimeoutRef\.current\)/);
assert.match(component, /onMouseLeave=\{\(\) => setHoverPaused\(false\)\}/);
assert.match(component, /onBlurCapture=\{handleBlur\}/);
assert.match(component, /target\.matches\(":focus-visible"\)/);
assert.match(component, /document\.visibilityState === "visible"/);
assert.match(component, /track\.scrollTo\(/, "Autoplay must move only the internal scroller");

console.log("carousel-autoplay-tests OK");
