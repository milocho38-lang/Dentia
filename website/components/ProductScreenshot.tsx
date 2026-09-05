import Image, { type StaticImageData } from "next/image";

export function ProductScreenshot({
  src,
  alt,
  priority = false,
  className = "",
}: {
  src: StaticImageData;
  alt: string;
  priority?: boolean;
  className?: string;
}) {
  return (
    <figure className={`product-screenshot ${className}`}>
      <div className="product-screenshot__bar" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <Image
        src={src}
        alt={alt}
        priority={priority}
        sizes="(max-width: 760px) 94vw, (max-width: 1100px) 84vw, 1200px"
      />
    </figure>
  );
}
