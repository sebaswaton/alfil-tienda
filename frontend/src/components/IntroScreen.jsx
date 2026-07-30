import { useEffect, useState } from "react";
import "./IntroScreen.css";

const SEEN_KEY = "hwstore_intro_seen";

export default function IntroScreen() {
  const [visible, setVisible] = useState(() => {
    if (typeof sessionStorage !== "undefined" && sessionStorage.getItem(SEEN_KEY)) return false;
    // If the tab loads in the background, timers get throttled and the intro
    // can get stuck covering the page. Skip it entirely in that case.
    if (typeof document !== "undefined" && document.visibilityState === "hidden") {
      try { sessionStorage.setItem(SEEN_KEY, "1"); } catch {}
      return false;
    }
    return true;
  });
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    if (!visible) return;

    document.body.style.overflow = "hidden";

    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;
      try { sessionStorage.setItem(SEEN_KEY, "1"); } catch {}
      document.body.style.overflow = "";
      setVisible(false);
    };

    const exitT = setTimeout(() => setExiting(true), 1750);
    const doneT = setTimeout(finish, 2600);
    // Hard safety net: never let the overlay linger, even if timers were throttled.
    const hardT = setTimeout(finish, 6000);
    // If the user comes back to a tab whose timers were throttled, wrap it up fast.
    const onVisible = () => {
      if (document.visibilityState === "visible") {
        setExiting(true);
        setTimeout(finish, 900);
      }
    };
    document.addEventListener("visibilitychange", onVisible);

    return () => {
      clearTimeout(exitT);
      clearTimeout(doneT);
      clearTimeout(hardT);
      document.removeEventListener("visibilitychange", onVisible);
      document.body.style.overflow = "";
    };
  }, [visible]);

  if (!visible) return null;

  return (
    <div className={"intro" + (exiting ? " intro--exit" : "")} aria-hidden="true">
      <div className="intro__panel intro__panel--top" />
      <div className="intro__panel intro__panel--bottom" />

      <div className="intro__content">
        <img src={`${import.meta.env.BASE_URL}hw-store-peru-logo.svg`} alt="" className="intro__logo" />
        <div className="intro__tagline">Tecnología para empresas</div>
      </div>
    </div>
  );
}
