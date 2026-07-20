import { useEffect, useRef, useState } from "react";

/**
 * Counts up to `target` once the element scrolls into view. `target` may
 * start at 0 while async data is still loading and change later — the
 * observer reads the latest value via a ref (not a closure) so it never
 * gets stuck animating to a stale 0.
 * Returns [ref, value].
 */
export function useCountUp(target, duration = 1400) {
  const ref = useRef(null);
  const [value, setValue] = useState(0);
  const targetRef = useRef(target);
  const hasIntersected = useRef(false);
  const rafId = useRef(null);

  targetRef.current = target;

  const animateTo = (to) => {
    cancelAnimationFrame(rafId.current);
    const start = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(Math.round(eased * to));
      if (t < 1) rafId.current = requestAnimationFrame(tick);
    };
    rafId.current = requestAnimationFrame(tick);
  };

  // Set up the observer once. When it intersects, animate to whatever the
  // *current* target is (via targetRef), not whatever it was at mount time.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const trigger = () => {
      hasIntersected.current = true;
      if (targetRef.current > 0) animateTo(targetRef.current);
    };

    if (typeof IntersectionObserver === "undefined") {
      trigger();
      return;
    }

    const obs = new IntersectionObserver(
      (entries) => entries.forEach((e) => {
        if (e.isIntersecting) {
          trigger();
          obs.disconnect();
        }
      }),
      { threshold: 0.4 }
    );
    obs.observe(el);
    return () => obs.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // If target changes after we've already intersected (e.g. it was 0 at
  // first paint and the real value arrived moments later), re-animate.
  useEffect(() => {
    if (hasIntersected.current && target > 0) animateTo(target);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target]);

  useEffect(() => () => cancelAnimationFrame(rafId.current), []);

  return [ref, value];
}
