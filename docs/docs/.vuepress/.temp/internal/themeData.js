export const themeData = JSON.parse("{\"repo\":\"heig-tin-info/baygon\",\"docsDir\":\"docs\",\"navbar\":[{\"text\":\"Guide\",\"link\":\"/guide/\"},{\"text\":\"Baygon\",\"link\":\"https://pypi.org/project/baygon/\"}],\"sidebar\":[{\"text\":\"Guide\",\"link\":\"/guide/\",\"children\":[{\"text\":\"Getting Started\",\"link\":\"/guide/\"},{\"text\":\"Syntax\",\"link\":\"/guide/syntax.md\"},{\"text\":\"Scripting\",\"link\":\"/guide/scripting.md\"},{\"text\":\"Academic Use\",\"link\":\"/guide/score.md\"},{\"text\":\"Advanced\",\"link\":\"/guide/advanced.md\"}]}],\"locales\":{\"/\":{\"selectLanguageName\":\"English\"}},\"colorMode\":\"auto\",\"colorModeSwitch\":true,\"logo\":null,\"selectLanguageText\":\"Languages\",\"selectLanguageAriaLabel\":\"Select language\",\"sidebarDepth\":2,\"editLink\":true,\"editLinkText\":\"Edit this page\",\"lastUpdated\":true,\"lastUpdatedText\":\"Last Updated\",\"contributors\":true,\"contributorsText\":\"Contributors\",\"notFound\":[\"There's nothing here.\",\"How did we get here?\",\"That's a Four-Oh-Four.\",\"Looks like we've got some broken links.\"],\"backToHome\":\"Take me home\",\"openInNewWindow\":\"open in new window\",\"toggleColorMode\":\"toggle color mode\",\"toggleSidebar\":\"toggle sidebar\"}")

if (import.meta.webpackHot) {
  import.meta.webpackHot.accept()
  if (__VUE_HMR_RUNTIME__.updateThemeData) {
    __VUE_HMR_RUNTIME__.updateThemeData(themeData)
  }
}

if (import.meta.hot) {
  import.meta.hot.accept(({ themeData }) => {
    __VUE_HMR_RUNTIME__.updateThemeData(themeData)
  })
}
