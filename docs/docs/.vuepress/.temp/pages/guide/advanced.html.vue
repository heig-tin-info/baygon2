<template><div><h1 id="advanced" tabindex="-1"><a class="header-anchor" href="#advanced"><span>Advanced</span></a></h1>
<h2 id="test-on-source-files" tabindex="-1"><a class="header-anchor" href="#test-on-source-files"><span>Test on source files</span></a></h2>
<p>You may want to execute tests on source files. This is possible by using <code v-pre>cat</code> as executable:</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span></span>
<span class="line"><span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test function foo</span>
<span class="line">    <span class="token key atrule">executable</span><span class="token punctuation">:</span> cat</span>
<span class="line">    <span class="token key atrule">stdin</span><span class="token punctuation">:</span> foo.c</span>
<span class="line">    <span class="token key atrule">stdout</span><span class="token punctuation">:</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">regex</span><span class="token punctuation">:</span> void\s+foo\s<span class="token important">*\(\s*int\s+\w+\)</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div></div></template>


