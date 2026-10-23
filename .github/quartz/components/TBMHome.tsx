import { QuartzComponent, QuartzComponentConstructor } from "./types"
// @ts-ignore
import script from "./scripts/tbmhome.inline"

// Оживляє головну сторінку TBM Енциклопедії:
//  • #tbm-stack  — стопка з 4 обкладинок (щодня інші), веде на Полицю
//  • #tbm-daily  — «Альбом дня» + кнопка «Інший»
// Дані — explore/data.json (той самий файл, що використовує Полиця).
// На інших сторінках нічого не робить.

const TBMHome: QuartzComponent = () => null

TBMHome.afterDOMLoaded = script

export default (() => TBMHome) satisfies QuartzComponentConstructor
