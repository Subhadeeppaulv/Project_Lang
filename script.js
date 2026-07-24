// ===================================================================
// PROJECT LANG — site script
// No frameworks, no build step — just the DOM.
// ===================================================================

document.addEventListener("DOMContentLoaded", () => {
  initNavToggle();
  initDocsSidebar();
  initScrollSpy();
  initCopyButtons();
});

// ---- mobile nav toggle ----
function initNavToggle() {
  const toggle = document.querySelector(".nav-toggle");
  const links = document.querySelector(".nav-links");
  if (!toggle || !links) return;

  toggle.addEventListener("click", () => {
    const isOpen = links.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });

  // close the menu after picking a link (mobile)
  links.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      links.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    });
  });
}

// ---- docs sidebar toggle (mobile) ----
function initDocsSidebar() {
  const toggle = document.querySelector(".mobile-docs-toggle");
  const sidebar = document.querySelector(".docs-sidebar");
  if (!toggle || !sidebar) return;

  toggle.addEventListener("click", () => {
    const isOpen = sidebar.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(isOpen));
    toggle.textContent = isOpen ? "Hide contents ▲" : "Contents ▼";
  });
}

// ---- highlight the current section in the docs sidebar while scrolling ----
function initScrollSpy() {
  const sections = document.querySelectorAll(".doc-section[id]");
  const sidebarLinks = document.querySelectorAll(".docs-sidebar a");
  if (!sections.length || !sidebarLinks.length) return;

  const linkFor = (id) =>
    document.querySelector(`.docs-sidebar a[href="#${id}"]`);

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const link = linkFor(entry.target.id);
        if (!link) return;
        if (entry.isIntersecting) {
          sidebarLinks.forEach((l) => l.classList.remove("active"));
          link.classList.add("active");
        }
      });
    },
    { rootMargin: "-20% 0px -70% 0px", threshold: 0 }
  );

  sections.forEach((section) => observer.observe(section));
}

// ---- copy button on every <pre> code block ----
function initCopyButtons() {
  document.querySelectorAll("pre").forEach((pre) => {
    // skip the hero's decorative terminal card, it's not meant to be copied
    if (pre.closest(".code-card")) return;

    const btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.type = "button";
    btn.textContent = "Copy";
    btn.setAttribute("aria-label", "Copy code to clipboard");
    pre.appendChild(btn);

    btn.addEventListener("click", async () => {
      const text = pre.innerText.replace(/Copy\s*$/, "").trim();
      try {
        await navigator.clipboard.writeText(text);
        btn.textContent = "Copied";
        btn.classList.add("copied");
      } catch (err) {
        btn.textContent = "Press Ctrl+C";
      }
      setTimeout(() => {
        btn.textContent = "Copy";
        btn.classList.remove("copied");
      }, 1800);
    });
  });
}
