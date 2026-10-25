// Скрипт головної сторінки TBM (підключається з TBMHome.tsx)
let cache: any = null

const esc = (s: any) =>
  String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] as string,
  )

const pick = (n: number, salt: number) => (Math.imul(n + 1, 2654435761) ^ salt) >>> 0

async function load(base: string) {
  if (!cache) {
    const r = await fetch(new URL("data.json", base).href)
    cache = await r.json()
  }
  return cache
}

function dailyCard(a: any, explore: string, kicker: string) {
  const cover = new URL("../" + (a.thumb || a.cover), explore).href
  const review = String(a.review || "").split(/\n\n+/)[0]
  const href = explore + "#album=" + encodeURIComponent(a.id)
  return `
    <a class="tbm-daily-cover" href="${href}" data-router-ignore><img src="${cover}" alt="${esc(a.title)}"></a>
    <div class="tbm-daily-body">
      <p class="tbm-daily-k">${esc(kicker)}</p>
      <h3>${esc(a.title)}</h3>
      <p class="tbm-daily-a">${esc(a.artist)}${a.year ? " · " + a.year : ""} · <span>${esc(a.cat)}</span></p>
      ${review ? `<p class="tbm-daily-r">${esc(review)}</p>` : ""}
      <div class="tbm-daily-act">
        <a class="tbm-btn" href="${href}" data-router-ignore>Відкрити на полиці</a>
        <button class="tbm-btn ghost" type="button" data-tbm-next>Інший →</button>
      </div>
    </div>`
}

async function init() {
  const stack = document.getElementById("tbm-stack") as HTMLAnchorElement | null
  const daily = document.getElementById("tbm-daily")
  if (!stack && !daily) return
  const explore = (stack?.href || new URL("explore/", location.href).href).split("#")[0]

  let data: any
  try {
    data = await load(explore)
  } catch {
    return
  }
  const withCover = data.albums.filter((a: any) => a.cover)
  if (!withCover.length) return
  const pool = withCover.filter((a: any) => a.review).length ? withCover.filter((a: any) => a.review) : withCover

  const day = Math.floor((Date.now() + 3 * 3600e3) / 864e5)
  const today = pool[pick(day, 0x5bd1e995) % pool.length]

  if (stack) {
    const chosen: any[] = []
    for (let k = 0; chosen.length < 4 && k < 50; k++) {
      const a = withCover[pick(day * 7 + k, 0x27d4eb2d) % withCover.length]
      if (a.id !== today.id && !chosen.includes(a)) chosen.push(a)
    }
    const sleeves = chosen
      .map((a, i) => {
        const img = `<img src="${new URL("../" + a.cover, explore).href}" alt="" loading="lazy">`
        return (i === 3 ? '<span class="tbm-disc"></span>' : "") + `<span class="tbm-sleeve s${i}">${img}</span>`
      })
      .join("")
    stack.innerHTML = `<span class="tbm-stack-art">${sleeves}</span>
      <span class="tbm-stack-label">Полиця · ${data.albums.length} альбомів →</span>`
  }

  if (daily) {
    const date = new Date().toLocaleDateString("uk-UA", { day: "numeric", month: "long" })
    daily.innerHTML = dailyCard(today, explore, "Альбом дня · " + date)
    daily.onclick = (e) => {
      const t = e.target as HTMLElement
      if (!t.closest("[data-tbm-next]")) return
      let a = today
      while (a.id === today.id && pool.length > 1) a = pool[Math.floor(Math.random() * pool.length)]
      daily.innerHTML = dailyCard(a, explore, "Випадковий альбом")
    }
  }
}

document.addEventListener("nav", init)
