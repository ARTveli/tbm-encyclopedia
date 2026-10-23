import { QuartzConfig } from "./quartz/cfg"
import * as Plugin from "./quartz/plugins"

/**
 * Quartz 4 Configuration
 *
 * See https://quartz.jzhao.xyz/configuration for more information.
 */
const config: QuartzConfig = {
  configuration: {
    pageTitle: "TBM Енциклопедія",
    pageTitleSuffix: "",
    enableSPA: true,
    enablePopovers: true,
    analytics: {
      provider: "plausible",
    },
    locale: "uk-UA",
    baseUrl: "artveli.github.io/tbm-encyclopedia",
    socialImage: "./static/og-image.png",
    ignorePatterns: ["private",
  "templates",
  ".obsidian",
  "_originals",
  "_originals/**",
  "copilot",
  "copilot/**",
  "media-lib",
  "media-lib/**",],
    defaultDateType: "modified",
    theme: {
      fontOrigin: "googleFonts",
      cdnCaching: true,
      typography: {
        header: "Schibsted Grotesk",
        body: "Schibsted Grotesk",
        code: "IBM Plex Mono",
      },
      colors: {
        lightMode: {
          light: "#f4efe6",
          lightgray: "#e3dacb",
          gray: "#8f8576",
          darkgray: "#3a342c",
          dark: "#1d1a16",
          secondary: "#b4432b",
          tertiary: "#d0694f",
          highlight: "rgba(180, 67, 43, 0.07)",
          textHighlight: "#f2c94c66",
        },
        darkMode: {
          light: "#14120f",
          lightgray: "#2f2a24",
          gray: "#8d8475",
          darkgray: "#d9d1c4",
          dark: "#efe8dc",
          secondary: "#e0694d",
          tertiary: "#f08a6e",
          highlight: "rgba(224, 105, 77, 0.1)",
          textHighlight: "#b3aa0288",
        },
      },
    },
  },
  plugins: {
    transformers: [
      Plugin.FrontMatter(),
      Plugin.CreatedModifiedDate({
        priority: ["frontmatter", "git", "filesystem"],
      }),
      Plugin.SyntaxHighlighting({
        theme: {
          light: "github-light",
          dark: "github-dark",
        },
        keepBackground: false,
      }),
      Plugin.ObsidianFlavoredMarkdown({ enableInHtmlEmbed: false }),
      Plugin.GitHubFlavoredMarkdown(),
      Plugin.TableOfContents(),
      Plugin.CrawlLinks({ markdownLinkResolution: "shortest" }),
      Plugin.Description(),
      Plugin.Latex({ renderEngine: "katex" }),
    ],
    filters: [Plugin.RemoveDrafts()],
    emitters: [
      Plugin.AliasRedirects(),
      Plugin.ComponentResources(),
      Plugin.ContentPage(),
      Plugin.FolderPage(),
      Plugin.TagPage(),
      Plugin.ContentIndex({
        enableSiteMap: true,
        enableRSS: true,
      }),
      Plugin.Assets(),
      Plugin.Static(),
      Plugin.Favicon(),
      Plugin.NotFoundPage(),
      // Comment out CustomOgImages to speed up build time
      // Plugin.CustomOgImages(),
    ],
  },
}

export default config
