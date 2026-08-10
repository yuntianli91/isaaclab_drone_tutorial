const root = document.documentElement;
const themeButton = document.querySelector("[data-theme-toggle]");
const menuButton = document.querySelector("[data-menu-toggle]");
const sidebar = document.querySelector(".sidebar");
const searchInput = document.querySelector("[data-search]");

const savedTheme = localStorage.getItem("isaaclab-zh-theme");
if (savedTheme) {
  root.dataset.theme = savedTheme;
}

themeButton?.addEventListener("click", () => {
  const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
  root.dataset.theme = nextTheme;
  localStorage.setItem("isaaclab-zh-theme", nextTheme);
});

menuButton?.addEventListener("click", () => {
  sidebar?.classList.toggle("open");
});

searchInput?.addEventListener("input", (event) => {
  const query = event.target.value.trim().toLocaleLowerCase("zh-CN");
  document.querySelectorAll(".sidebar [data-search-item]").forEach((item) => {
    const matches = item.textContent.toLocaleLowerCase("zh-CN").includes(query);
    item.style.display = matches ? "block" : "none";
  });
});

function escapeHtml(source) {
  return source
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function highlightTokens(source, pattern) {
  let highlighted = "";
  let previousEnd = 0;

  for (const match of source.matchAll(pattern)) {
    highlighted += escapeHtml(source.slice(previousEnd, match.index));
    const tokenType = Object.entries(match.groups).find(
      ([, value]) => value !== undefined,
    )[0];
    highlighted +=
      `<span class="syntax-${tokenType}">${escapeHtml(match[0])}</span>`;
    previousEnd = match.index + match[0].length;
  }

  return highlighted + escapeHtml(source.slice(previousEnd));
}

const pythonPattern = new RegExp(
  [
    String.raw`(?<string>"""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')`,
    String.raw`(?<comment>#[^\n]*)`,
    String.raw`(?<keyword>\b(?:False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b)`,
    String.raw`(?<number>\b\d+(?:\.\d+)?\b)`,
  ].join("|"),
  "g",
);

const bashPattern = new RegExp(
  [
    String.raw`(?<string>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')`,
    String.raw`(?<comment>#[^\n]*)`,
    String.raw`(?<option>(?<![\w-])--?[\w-]+)`,
    String.raw`(?<keyword>\b(?:case|do|done|elif|else|esac|fi|for|function|if|in|then|until|while)\b)`,
    String.raw`(?<number>\b\d+(?:\.\d+)?\b)`,
  ].join("|"),
  "g",
);

document.querySelectorAll("code.language-python").forEach((code) => {
  code.innerHTML = highlightTokens(code.textContent, pythonPattern);
});

document.querySelectorAll("code.language-bash").forEach((code) => {
  code.innerHTML = highlightTokens(code.textContent, bashPattern);
});

document.querySelectorAll(".code-block").forEach((block) => {
  const button = document.createElement("button");
  button.className = "copy-button";
  button.type = "button";
  button.textContent = "复制";
  button.addEventListener("click", async () => {
    const code = block.querySelector("code, pre")?.textContent ?? "";
    await navigator.clipboard.writeText(code);
    button.textContent = "已复制";
    setTimeout(() => {
      button.textContent = "复制";
    }, 1200);
  });
  block.appendChild(button);
});
