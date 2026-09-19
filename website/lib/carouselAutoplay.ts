export const AUTOPLAY_DELAY_MS = 6000;
export const MANUAL_INTERACTION_PAUSE_MS = 10000;

export type CarouselAutoplayState = {
  reducedMotion: boolean;
  userPaused: boolean;
  interactionPaused: boolean;
  hoverPaused: boolean;
  focusPaused: boolean;
  pageVisible: boolean;
  inViewport: boolean;
};

export function shouldRunCarouselAutoplay(state: CarouselAutoplayState) {
  return (
    !state.reducedMotion
    && !state.userPaused
    && !state.interactionPaused
    && !state.hoverPaused
    && !state.focusPaused
    && state.pageVisible
    && state.inViewport
  );
}

export function getNextCarouselSlideIndex(activeIndex: number, slideCount: number) {
  if (slideCount <= 0) return 0;
  return (activeIndex + 1) % slideCount;
}
