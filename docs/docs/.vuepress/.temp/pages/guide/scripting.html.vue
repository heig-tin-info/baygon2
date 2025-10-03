<template><div><h1 id="scripting" tabindex="-1"><a class="header-anchor" href="#scripting"><span>Scripting</span></a></h1>
<p>You can use Baygon as a library to write your own test runner. This is useful if you want to write your own test runner or if you want to use Baygon in a CI/CD pipeline.</p>
<p>Here is an example of a test runner using Baygon:</p>
<div class="language-python line-numbers-mode" data-highlighter="prismjs" data-ext="py" data-title="py"><pre v-pre><code><span class="line"><span class="token keyword">from</span> pathlib <span class="token keyword">import</span> Path</span>
<span class="line"><span class="token keyword">import</span> baygon</span>
<span class="line"></span>
<span class="line">ts <span class="token operator">=</span> baygon<span class="token punctuation">.</span>TestSuite<span class="token punctuation">(</span><span class="token punctuation">{</span></span>
<span class="line">        <span class="token string">'filters'</span><span class="token punctuation">:</span> <span class="token punctuation">{</span><span class="token string">'uppercase'</span><span class="token punctuation">:</span> <span class="token boolean">True</span><span class="token punctuation">}</span><span class="token punctuation">,</span></span>
<span class="line">        <span class="token string">'tests'</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token punctuation">{</span></span>
<span class="line">            <span class="token string">'args'</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token string">'--version'</span><span class="token punctuation">]</span><span class="token punctuation">,</span></span>
<span class="line">            <span class="token string">'stderr'</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token punctuation">{</span><span class="token string">'contains'</span><span class="token punctuation">:</span> <span class="token string">'VERSION'</span><span class="token punctuation">}</span><span class="token punctuation">]</span></span>
<span class="line">        <span class="token punctuation">}</span><span class="token punctuation">]</span></span>
<span class="line">    <span class="token punctuation">}</span><span class="token punctuation">,</span> executable<span class="token operator">=</span>Path<span class="token punctuation">(</span><span class="token string">'myapp'</span><span class="token punctuation">)</span><span class="token punctuation">)</span></span>
<span class="line">t <span class="token operator">=</span> ts<span class="token punctuation">.</span>run<span class="token punctuation">(</span><span class="token punctuation">)</span></span>
<span class="line"></span>
<span class="line"><span class="token keyword">assert</span><span class="token punctuation">(</span>t<span class="token punctuation">,</span> <span class="token punctuation">[</span><span class="token punctuation">[</span><span class="token punctuation">]</span><span class="token punctuation">]</span><span class="token punctuation">)</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><h2 id="validation" tabindex="-1"><a class="header-anchor" href="#validation"><span>Validation</span></a></h2>
<p>You can validate a Baygon configuration file with the <code v-pre>baygon.Schema</code> function:</p>
<div class="language-python line-numbers-mode" data-highlighter="prismjs" data-ext="py" data-title="py"><pre v-pre><code><span class="line"><span class="token keyword">import</span> baygon</span>
<span class="line"></span>
<span class="line">data <span class="token operator">=</span> baygon<span class="token punctuation">.</span>Schema<span class="token punctuation">(</span><span class="token punctuation">{</span></span>
<span class="line">    <span class="token string">'version'</span><span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">,</span></span>
<span class="line">    <span class="token string">'tests'</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token punctuation">{</span></span>
<span class="line">        <span class="token string">'name'</span><span class="token punctuation">:</span> <span class="token string">'Test'</span><span class="token punctuation">,</span></span>
<span class="line">        <span class="token string">'exit'</span><span class="token punctuation">:</span> <span class="token number">0</span></span>
<span class="line">    <span class="token punctuation">}</span><span class="token punctuation">]</span></span>
<span class="line"><span class="token punctuation">}</span><span class="token punctuation">)</span></span>
<span class="line"></span>
<span class="line"><span class="token keyword">assert</span><span class="token punctuation">(</span>data<span class="token punctuation">[</span><span class="token string">'version'</span><span class="token punctuation">]</span><span class="token punctuation">,</span> <span class="token number">1</span><span class="token punctuation">)</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div></div></template>


