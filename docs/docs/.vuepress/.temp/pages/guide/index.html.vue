<template><div><h1 id="what-is-baygon" tabindex="-1"><a class="header-anchor" href="#what-is-baygon"><span>What is Baygon?</span></a></h1>
<p><strong>Baygon</strong> is a minimalistic test framework for any types of executables. It provides a simple way of testing code with a <a href="https://en.wikipedia.org/wiki/JSON" target="_blank" rel="noopener noreferrer">JSON</a> or a <a href="https://en.wikipedia.org/wiki/YAML" target="_blank" rel="noopener noreferrer">YAML</a> description of tests.</p>
<p>It is mainly designed for simple tests in academic environments, but it can be used for any kind of tests.</p>
<p>Points can be assigned to tests, group of tests or automatically distributed based on the number of tests. The total earned points can be used to calculate the final assignment grade.</p>
<div class="hint-container warning">
<p class="hint-container-title">Warning</p>
<p>Baygon is currently in <code v-pre>beta</code> stage. It's ready to be used for building functional tests, but the config and API are not stable enough, which is likely to have breaking changes between minor releases.</p>
</div>
<h2 id="how-it-works" tabindex="-1"><a class="header-anchor" href="#how-it-works"><span>How it works</span></a></h2>
<p>Baygon is a CLI tool that runs tests described in a JSON or YAML file. It can be used to test any kind of executable, including binaries, scripts, and even web applications. It's designed to be used for student assignments.</p>
<p>Based on the description file, a <code v-pre>TestSuite</code> is built. A <code v-pre>TestSuite</code> is a collection of <code v-pre>TestCases</code> that are executed sequentially. Each <code v-pre>TestCase</code> is a collection of <code v-pre>TestSteps</code> that are executed sequentially.</p>
<p>By default Baygon will run all the tests in the description file.</p>
<h2 id="what-a-strange-name" tabindex="-1"><a class="header-anchor" href="#what-a-strange-name"><span>What a strange name!</span></a></h2>
<p>Baygon is a brand of insecticide popularized in the 80s by the commercial ads featuring Michel Leeb. The name was chosen because it's a simple and short name that is easy to remember. And Baygon is meant to kill bugs in your code!</p>
<h2 id="get-started" tabindex="-1"><a class="header-anchor" href="#get-started"><span>Get started</span></a></h2>
<p>Let's say you have a C program you want to test:</p>
<div class="language-c line-numbers-mode" data-highlighter="prismjs" data-ext="c" data-title="c"><pre v-pre><code><span class="line"><span class="token macro property"><span class="token directive-hash">#</span><span class="token directive keyword">include</span> <span class="token string">&lt;stdio.h></span></span></span>
<span class="line"><span class="token macro property"><span class="token directive-hash">#</span><span class="token directive keyword">include</span> <span class="token string">&lt;string.h></span></span></span>
<span class="line"><span class="token macro property"><span class="token directive-hash">#</span><span class="token directive keyword">include</span> <span class="token string">&lt;stdlib.h></span></span></span>
<span class="line"></span>
<span class="line"><span class="token keyword">int</span> <span class="token function">main</span><span class="token punctuation">(</span><span class="token keyword">int</span> argc<span class="token punctuation">,</span> <span class="token keyword">char</span> <span class="token operator">*</span>argv<span class="token punctuation">[</span><span class="token punctuation">]</span><span class="token punctuation">)</span> <span class="token punctuation">{</span></span>
<span class="line">    <span class="token keyword">if</span> <span class="token punctuation">(</span>argc <span class="token operator">></span> <span class="token number">1</span> <span class="token operator">&amp;&amp;</span> <span class="token function">strcmp</span><span class="token punctuation">(</span>argv<span class="token punctuation">[</span><span class="token number">1</span><span class="token punctuation">]</span><span class="token punctuation">,</span> <span class="token string">"--version"</span><span class="token punctuation">)</span> <span class="token operator">==</span> <span class="token number">0</span><span class="token punctuation">)</span> <span class="token punctuation">{</span></span>
<span class="line">        <span class="token function">fprintf</span><span class="token punctuation">(</span><span class="token constant">stderr</span><span class="token punctuation">,</span> <span class="token string">"Version 0.1.1\n"</span><span class="token punctuation">)</span><span class="token punctuation">;</span></span>
<span class="line">        <span class="token keyword">return</span> <span class="token number">0</span><span class="token punctuation">;</span></span>
<span class="line">    <span class="token punctuation">}</span></span>
<span class="line">    <span class="token keyword">if</span> <span class="token punctuation">(</span>argc <span class="token operator">!=</span> <span class="token number">2</span> <span class="token operator">+</span> <span class="token number">1</span><span class="token punctuation">)</span> <span class="token keyword">return</span> <span class="token number">1</span><span class="token punctuation">;</span></span>
<span class="line">    <span class="token function">printf</span><span class="token punctuation">(</span><span class="token string">"%d"</span><span class="token punctuation">,</span> <span class="token function">atoi</span><span class="token punctuation">(</span>argv<span class="token punctuation">[</span><span class="token number">1</span><span class="token punctuation">]</span><span class="token punctuation">)</span> <span class="token operator">+</span> <span class="token function">atoi</span><span class="token punctuation">(</span>argv<span class="token punctuation">[</span><span class="token number">2</span><span class="token punctuation">]</span><span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span></span>
<span class="line"><span class="token punctuation">}</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><p>You then need to write a test file that can be named <code v-pre>t.yaml</code>, <code v-pre>t.json</code>, <code v-pre>test.yaml</code>, <code v-pre>test.json</code>, <code v-pre>tests.yml</code> or <code v-pre>test.json</code>. Baygon is gonna find it. Inside this file you describe each individual functional test:</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span></span>
<span class="line"><span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Arguments check</span>
<span class="line">    <span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> No errors if two arguments</span>
<span class="line">        <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token number">1</span><span class="token punctuation">,</span> <span class="token number">2</span><span class="token punctuation">]</span></span>
<span class="line">        <span class="token key atrule">exit</span><span class="token punctuation">:</span> <span class="token number">0</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Error if less than two arguments</span>
<span class="line">        <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token number">1</span><span class="token punctuation">]</span></span>
<span class="line">        <span class="token key atrule">exit</span><span class="token punctuation">:</span> <span class="token number">1</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Stdout is the sum of arguments</span>
<span class="line">    <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token number">1</span><span class="token punctuation">,</span> <span class="token number">2</span><span class="token punctuation">]</span></span>
<span class="line">    <span class="token key atrule">stdout</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token punctuation">]</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Version on stderr</span>
<span class="line">    <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token string">'--version'</span><span class="token punctuation">]</span></span>
<span class="line">    <span class="token key atrule">stderr</span><span class="token punctuation">:</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">regex</span><span class="token punctuation">:</span> <span class="token string">'\b\d\.\d\.\d\b'</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">contains</span><span class="token punctuation">:</span> <span class="token string">'Version'</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><p>To be able to run the tests, simply install <a href="https://pypi.org/project/baygon/" target="_blank" rel="noopener noreferrer">Baygon</a>:</p>
<div class="language-text line-numbers-mode" data-highlighter="prismjs" data-ext="text" data-title="text"><pre v-pre><code><span class="line">pip install baygon</span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div></div></div><p>Then build and test you application:</p>
<div class="language-text line-numbers-mode" data-highlighter="prismjs" data-ext="text" data-title="text"><pre v-pre><code><span class="line">$ cc app.c -o a.out</span>
<span class="line">$ baygon -v ./a.out</span>
<span class="line">Test 1: Arguments check</span>
<span class="line">  Test 1.1: No errors if two arguments.......... PASSED</span>
<span class="line">  Test 1.2: Error if less than two arguments.... PASSED</span>
<span class="line">Test 2: Stdout is the sum of arguments.......... PASSED</span>
<span class="line">Test 3: Version on stderr....................... PASSED</span>
<span class="line"></span>
<span class="line">Ran 4 tests in 0.01s.</span>
<span class="line"></span>
<span class="line">ok.</span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><div class="hint-container tip">
<p class="hint-container-title">Tips</p>
<p>You may need to use <code v-pre>pip3</code> instead of <code v-pre>pip</code> depending on your system.</p>
</div>
</div></template>


