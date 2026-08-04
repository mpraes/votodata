(() => {
  const tips = () => document.querySelectorAll("details.info-tip");

  document.addEventListener("toggle", (event) => {
    const el = event.target;
    if (!(el instanceof HTMLDetailsElement) || !el.classList.contains("info-tip") || !el.open) {
      return;
    }
    tips().forEach((other) => {
      if (other !== el) other.open = false;
    });
  }, true);

  document.addEventListener("pointerdown", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    if (target.closest("details.info-tip")) return;
    tips().forEach((tip) => {
      tip.open = false;
    });
  });
})();
