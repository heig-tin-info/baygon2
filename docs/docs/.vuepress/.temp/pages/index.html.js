import comp from "/home/ycr/baygon/docs/docs/.vuepress/.temp/pages/index.html.vue"
const data = JSON.parse("{\"path\":\"/\",\"title\":\"Home\",\"lang\":\"en-US\",\"frontmatter\":{\"home\":true,\"title\":\"Home\",\"heroImage\":\"/baygon.svg\",\"actions\":[{\"text\":\"Get Started\",\"link\":\"/guide\",\"type\":\"primary\"},{\"text\":\"Syntax\",\"link\":\"/guide/syntax.md\",\"type\":\"secondary\"}],\"footer\":\"MIT Licensed | Copyright © HEIG-VD 2021-present\"},\"headers\":[],\"git\":{\"updatedTime\":1667915383000,\"contributors\":[{\"name\":\"Yves Chevallier\",\"email\":\"52489316+yves-chevallier@users.noreply.github.com\",\"commits\":1},{\"name\":\"Yves Chevallier\",\"email\":\"yves.chevallier@heig-vd.ch\",\"commits\":1}]},\"filePathRelative\":\"README.md\"}")
export { comp, data }

if (import.meta.webpackHot) {
  import.meta.webpackHot.accept()
  if (__VUE_HMR_RUNTIME__.updatePageData) {
    __VUE_HMR_RUNTIME__.updatePageData(data)
  }
}

if (import.meta.hot) {
  import.meta.hot.accept(({ data }) => {
    __VUE_HMR_RUNTIME__.updatePageData(data)
  })
}
