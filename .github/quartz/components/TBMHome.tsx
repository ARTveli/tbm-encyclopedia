import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import HeadConstructor from "./Head"
// @ts-ignore
import script from "./scripts/tbmhome.inline"

// Оживляє головну сторінку TBM Енциклопедії:
//  • #tbm-daily  — «Альбом дня» + кнопка «Інший»
// Дані — explore/data.json (той самий файл, що використовує Полиця).
// На інших сторінках нічого не робить.

const TBMHome: QuartzComponent = () => null

TBMHome.afterDOMLoaded = script

export default (() => TBMHome) satisfies QuartzComponentConstructor

// Head з картинкою прев'ю для окремої сторінки: якщо у frontmatter є socialImage
// (обкладинка альбому), вона підставляється в og:image / twitter:image
// замість спільної картинки сайту.
export const TBMHead = (() => {
  const Base = HeadConstructor()
  const Head: QuartzComponent = (props: QuartzComponentProps) => {
    const vnode = Base(props) as any
    const img = props.fileData.frontmatter?.socialImage as string | undefined
    if (!img) return vnode
    const abs = /^https?:\/\//.test(img) ? img : `https://${props.cfg.baseUrl}/${encodeURI(img)}`
    const ext = (img.split(".").pop() || "jpg").toLowerCase()
    const type = `image/${ext === "jpg" ? "jpeg" : ext}`
    const walk = (n: any) => {
      if (!n || typeof n !== "object") return
      if (Array.isArray(n)) return n.forEach(walk)
      const p = n.props || {}
      if (n.type === "meta") {
        if (p.property === "og:image" || p.property === "og:image:url" || p.name === "twitter:image") p.content = abs
        if (p.property === "og:image:type") p.content = type
      }
      walk(p.children)
    }
    walk(vnode)
    return vnode
  }
  Head.css = Base.css
  Head.beforeDOMLoaded = Base.beforeDOMLoaded
  Head.afterDOMLoaded = Base.afterDOMLoaded
  return Head
}) satisfies QuartzComponentConstructor
