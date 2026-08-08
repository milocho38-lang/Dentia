export const SIGNATURE_LOGICAL_WIDTH = 640;
export const SIGNATURE_LOGICAL_HEIGHT = 220;
export const SIGNATURE_MAX_PIXEL_RATIO = 2;

export function signatureCanvasDimensions(devicePixelRatio = 1) {
  const finiteRatio = Number.isFinite(devicePixelRatio) && devicePixelRatio > 0 ? devicePixelRatio : 1;
  const pixelRatio = Math.min(finiteRatio, SIGNATURE_MAX_PIXEL_RATIO);
  return {
    pixelRatio,
    width: Math.round(SIGNATURE_LOGICAL_WIDTH * pixelRatio),
    height: Math.round(SIGNATURE_LOGICAL_HEIGHT * pixelRatio),
  };
}
