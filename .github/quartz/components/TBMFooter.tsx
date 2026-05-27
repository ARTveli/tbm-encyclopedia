import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"

// Кастомний Footer для TBM Енциклопедії
// Замість стандартного Footer Quartz — наш з copyright, контактами і disclaimer

const TBMFooter: QuartzComponent = ({ displayClass }: QuartzComponentProps) => {
  const year = new Date().getFullYear()
  return (
    <footer class={`${displayClass ?? ""}`}>
      <p style="text-align: center; margin: 0.5em 0; font-size: 0.85em; line-height: 1.6;">
        © {year} Артем Величковський
        {" • "}
        <a href="mailto:artveli@gmail.com">artveli@gmail.com</a>
        {" • "}
        <a href="https://instagram.com/artveli" target="_blank" rel="noopener noreferrer">Instagram @artveli</a>
      </p>
      <p style="text-align: center; margin: 0.5em 0; font-size: 0.75em; opacity: 0.7; max-width: 700px; margin-left: auto; margin-right: auto;">
        Авторські права на оригінальні тексти, обкладинки та фотографії належать їх власникам.
        Цей сайт — некомерційний фанатський переклад книги <em>Three Blind Mice — Complete Disc Guide</em> для збереження джазової спадщини лейблу TBM.
      </p>
    </footer>
  )
}

export default (() => TBMFooter) satisfies QuartzComponentConstructor
