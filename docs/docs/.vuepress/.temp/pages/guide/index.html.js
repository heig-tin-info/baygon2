import comp from "/home/ycr/baygon/docs/docs/.vuepress/.temp/pages/guide/index.html.vue"
const data = JSON.parse("{\"path\":\"/guide/\",\"title\":\"What is Baygon?\",\"lang\":\"en-US\",\"frontmatter\":{},\"headers\":[{\"level\":2,\"title\":\"How it works\",\"slug\":\"how-it-works\",\"link\":\"#how-it-works\",\"children\":[]},{\"level\":2,\"title\":\"What a strange name!\",\"slug\":\"what-a-strange-name\",\"link\":\"#what-a-strange-name\",\"children\":[]},{\"level\":2,\"title\":\"Get started\",\"slug\":\"get-started\",\"link\":\"#get-started\",\"children\":[]}],\"git\":{\"updatedTime\":1728487316000,\"contributors\":[{\"name\":\"Yves Chevallier\",\"email\":\"yves.chevallier@heig-vd.ch\",\"commits\":3}]},\"filePathRelative\":\"guide/README.md\"}")
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
