export const redirects = JSON.parse("{}")

export const routes = Object.fromEntries([
  ["/", { loader: () => import(/* webpackChunkName: "index.html" */"/home/ycr/baygon/docs/docs/.vuepress/.temp/pages/index.html.js"), meta: {"title":"Home"} }],
  ["/guide/", { loader: () => import(/* webpackChunkName: "guide_index.html" */"/home/ycr/baygon/docs/docs/.vuepress/.temp/pages/guide/index.html.js"), meta: {"title":"What is Baygon?"} }],
  ["/guide/advanced.html", { loader: () => import(/* webpackChunkName: "guide_advanced.html" */"/home/ycr/baygon/docs/docs/.vuepress/.temp/pages/guide/advanced.html.js"), meta: {"title":"Advanced"} }],
  ["/guide/contributing.html", { loader: () => import(/* webpackChunkName: "guide_contributing.html" */"/home/ycr/baygon/docs/docs/.vuepress/.temp/pages/guide/contributing.html.js"), meta: {"title":""} }],
  ["/guide/score.html", { loader: () => import(/* webpackChunkName: "guide_score.html" */"/home/ycr/baygon/docs/docs/.vuepress/.temp/pages/guide/score.html.js"), meta: {"title":"Academic Assignment"} }],
  ["/guide/scripting.html", { loader: () => import(/* webpackChunkName: "guide_scripting.html" */"/home/ycr/baygon/docs/docs/.vuepress/.temp/pages/guide/scripting.html.js"), meta: {"title":"Scripting"} }],
  ["/guide/syntax.html", { loader: () => import(/* webpackChunkName: "guide_syntax.html" */"/home/ycr/baygon/docs/docs/.vuepress/.temp/pages/guide/syntax.html.js"), meta: {"title":"Config File Syntax"} }],
  ["/404.html", { loader: () => import(/* webpackChunkName: "404.html" */"/home/ycr/baygon/docs/docs/.vuepress/.temp/pages/404.html.js"), meta: {"title":""} }],
]);

if (import.meta.webpackHot) {
  import.meta.webpackHot.accept()
  if (__VUE_HMR_RUNTIME__.updateRoutes) {
    __VUE_HMR_RUNTIME__.updateRoutes(routes)
  }
  if (__VUE_HMR_RUNTIME__.updateRedirects) {
    __VUE_HMR_RUNTIME__.updateRedirects(redirects)
  }
}

if (import.meta.hot) {
  import.meta.hot.accept(({ routes, redirects }) => {
    __VUE_HMR_RUNTIME__.updateRoutes(routes)
    __VUE_HMR_RUNTIME__.updateRedirects(redirects)
  })
}
