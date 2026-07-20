import { useEffect, useRef } from "react";

/**
 * Adds `is-visible` to the ref element once it scrolls into view.
 * Pair with the `.reveal` utility class. Runs once per element.
 */
export function useReveal(options = {}) {
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    if (typeof IntersectionObserver === "undefined") {
      el.classList.add("is-visible");
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px", ...options }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [options]);

  return ref;
}

/**
 * Reveals a container's direct children with a staggered delay.
 * Pass `deps` (e.g. [items.length]) so it re-observes once async data arrives.
 */
export function useStaggerReveal(step = 90, deps = []) {
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || el.children.length === 0) return;

    const children = Array.from(el.children);
    children.forEach((child, i) => {
      child.classList.add("reveal");
      child.style.setProperty("--reveal-delay", `${i * step}ms`);
    });

    if (typeof IntersectionObserver === "undefined") {
      children.forEach((c) => c.classList.add("is-visible"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -6% 0px" }
    );

    children.forEach((c) => observer.observe(c));
    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, ...deps]);

  return ref;
}
