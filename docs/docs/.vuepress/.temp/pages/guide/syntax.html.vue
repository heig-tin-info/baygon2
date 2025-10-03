<template><div><h1 id="config-file-syntax" tabindex="-1"><a class="header-anchor" href="#config-file-syntax"><span>Config File Syntax</span></a></h1>
<h2 id="base" tabindex="-1"><a class="header-anchor" href="#base"><span>Base</span></a></h2>
<p>Each config file should start with the version of the syntax which is <code v-pre>1</code>. Then the mandatory <code v-pre>tests</code> dictionary must exist. The following is a minimal example composed of 1 test which tests if the output is 3 when the binary is run with two arguments <code v-pre>1</code> and <code v-pre>2</code>:</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span></span>
<span class="line"><span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token number">1</span><span class="token punctuation">,</span> <span class="token number">2</span><span class="token punctuation">]</span></span>
<span class="line">    <span class="token key atrule">stdout</span><span class="token punctuation">:</span> <span class="token number">3</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><h2 id="filters" tabindex="-1"><a class="header-anchor" href="#filters"><span>Filters</span></a></h2>
<p>Global filters can be applied to all outputs of every tests. The outputs are <code v-pre>stdout</code> and <code v-pre>stderr</code>. Baygon features the following filters:</p>
<ul>
<li><code v-pre>uppercase</code>: All outputs are transformed into uppercase.</li>
<li><code v-pre>lowercase</code>: All outputs are transformed into lowercase.</li>
<li><code v-pre>trim</code>: All outputs are trimmed (spaces are removed from both ends, on each line</li>
<li><code v-pre>ignore-spaces</code>: All spaces are removed from all outputs.</li>
<li><code v-pre>regex</code>: A remplacement is made using regular expressions.</li>
<li><code v-pre>replace</code>: A remplacement is made using a string.</li>
</ul>
<p>If more than one filter is applied, they are applied in the order they are written.</p>
<p>In the following, both standard output and standard error will be in lowercase and every occurrences of <code v-pre>foo</code> or <code v-pre>foobar</code> will be replaced by <code v-pre>bar</code>:</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span></span>
<span class="line"><span class="token key atrule">filters</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token key atrule">lowercase</span><span class="token punctuation">:</span> <span class="token boolean important">true</span></span>
<span class="line">  <span class="token key atrule">regex</span><span class="token punctuation">:</span> <span class="token punctuation">[</span>foo(bar)<span class="token punctuation">?</span><span class="token punctuation">,</span> bar<span class="token punctuation">]</span></span>
<span class="line"><span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token number">1</span><span class="token punctuation">,</span> <span class="token number">2</span><span class="token punctuation">]</span></span>
<span class="line">    <span class="token key atrule">stdout</span><span class="token punctuation">:</span> <span class="token number">3</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><p>Filters can also be applied to a single test:</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span></span>
<span class="line"><span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token number">1</span><span class="token punctuation">,</span> <span class="token number">2</span><span class="token punctuation">]</span></span>
<span class="line">    <span class="token key atrule">stdout</span><span class="token punctuation">:</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">contains</span><span class="token punctuation">:</span> foo</span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">regex</span><span class="token punctuation">:</span> f(oo<span class="token punctuation">|</span>aa<span class="token punctuation">|</span>uu)</span>
<span class="line">    <span class="token key atrule">filters</span><span class="token punctuation">:</span></span>
<span class="line">      <span class="token key atrule">lowercase</span><span class="token punctuation">:</span> <span class="token boolean important">true</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><p>Or even at a stream output level:</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">stdout</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token punctuation">{</span> <span class="token key atrule">filters</span><span class="token punctuation">:</span> <span class="token punctuation">{</span> <span class="token key atrule">trim</span><span class="token punctuation">:</span> <span class="token boolean important">true</span> <span class="token punctuation">}</span><span class="token punctuation">,</span> <span class="token key atrule">equals</span><span class="token punctuation">:</span> <span class="token number">3</span> <span class="token punctuation">}</span><span class="token punctuation">]</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div></div></div><h2 id="naming" tabindex="-1"><a class="header-anchor" href="#naming"><span>Naming</span></a></h2>
<p>All tests can be optionally named:</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span></span>
<span class="line"><span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test functionality of the additionner</span>
<span class="line">    <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token punctuation">-</span><span class="token punctuation">-</span>add<span class="token punctuation">,</span> <span class="token number">40</span><span class="token punctuation">,</span> <span class="token number">2</span><span class="token punctuation">]</span></span>
<span class="line">    <span class="token key atrule">stdout</span><span class="token punctuation">:</span> <span class="token number">42</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test error if less than two arguments</span>
<span class="line">    <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token punctuation">]</span></span>
<span class="line">    <span class="token key atrule">exit</span><span class="token punctuation">:</span> <span class="token number">2</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><h2 id="groups-and-subgroups" tabindex="-1"><a class="header-anchor" href="#groups-and-subgroups"><span>Groups and subgroups</span></a></h2>
<p>Tests can be grouped into sub sections, by nesting each test into categories:</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span></span>
<span class="line"><span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Category 1</span>
<span class="line">    <span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token number">1</span><span class="token punctuation">,</span> <span class="token number">2</span><span class="token punctuation">]</span></span>
<span class="line">        <span class="token key atrule">stdout</span><span class="token punctuation">:</span> <span class="token number">3</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Category 2</span>
<span class="line">    <span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Subcategory 1</span>
<span class="line">        <span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">          <span class="token punctuation">-</span> <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token number">1</span><span class="token punctuation">,</span> <span class="token number">2</span><span class="token punctuation">]</span></span>
<span class="line">            <span class="token key atrule">stdout</span><span class="token punctuation">:</span> <span class="token number">3</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><h2 id="exit-status" tabindex="-1"><a class="header-anchor" href="#exit-status"><span>Exit status</span></a></h2>
<p>The exit status can be checked with the <code v-pre>exit</code> key followed with an integer. The following checks if the program returns 0</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span></span>
<span class="line"><span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">exit</span><span class="token punctuation">:</span> <span class="token number">0</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><h2 id="standard-outputs" tabindex="-1"><a class="header-anchor" href="#standard-outputs"><span>Standard outputs</span></a></h2>
<p>Both <code v-pre>stdout</code> and <code v-pre>stderr</code> can be tested against multiple conditions:</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">stdout</span><span class="token punctuation">:</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">contains</span><span class="token punctuation">:</span> foo <span class="token comment"># Must contain the word foo</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">regex</span><span class="token punctuation">:</span> f(oo<span class="token punctuation">|</span>aa<span class="token punctuation">|</span>uu) <span class="token comment"># Must match</span></span>
<span class="line">    <span class="token key atrule">stderr</span><span class="token punctuation">:</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">equals</span><span class="token punctuation">:</span> foobar <span class="token comment"># Must be exactly equal to foobar</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><h2 id="executable" tabindex="-1"><a class="header-anchor" href="#executable"><span>Executable</span></a></h2>
<p>In the case you want to specify a different executable name for a different test:</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test ./foo</span>
<span class="line">    <span class="token key atrule">executable</span><span class="token punctuation">:</span> ./foo</span>
<span class="line">    <span class="token key atrule">stdout</span><span class="token punctuation">:</span> I am Foo</span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test ./bar</span>
<span class="line">    <span class="token key atrule">executable</span><span class="token punctuation">:</span> ./bar</span>
<span class="line">    <span class="token key atrule">stderr</span><span class="token punctuation">:</span> I am bar</span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Group</span>
<span class="line">    <span class="token key atrule">executable</span><span class="token punctuation">:</span> ./baz</span>
<span class="line">    <span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test 1</span>
<span class="line">        <span class="token key atrule">exit</span><span class="token punctuation">:</span> <span class="token number">0</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><p>The executable is propagated through the test tree. But you cannot override an existing executable. The following is invalid:</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">executable</span><span class="token punctuation">:</span> ./foo</span>
<span class="line">    <span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">executable</span><span class="token punctuation">:</span> ./bar</span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><p>One approach is name the executable at the top level:</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span></span>
<span class="line"><span class="token key atrule">executable</span><span class="token punctuation">:</span> ./foobar</span>
<span class="line"><span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test ./foobar</span>
<span class="line">    <span class="token key atrule">exit</span><span class="token punctuation">:</span> <span class="token number">0</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><p>Or even from the shell:</p>
<div class="language-console line-numbers-mode" data-highlighter="prismjs" data-ext="console" data-title="console"><pre v-pre><code><span class="line">baygon ./foobar</span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div></div></div><p>Note that the working directory is the directory of the config file, except if you specify the executable from the shell. In this case the working directory is the current directory.</p>
<h2 id="configuration-file" tabindex="-1"><a class="header-anchor" href="#configuration-file"><span>Configuration file</span></a></h2>
<p>By default Baygon will look for a file named <code v-pre>baygon.yml</code> in the current directory. You can specify a different file with the <code v-pre>-c</code> or <code v-pre>--config</code> option:</p>
<div class="language-console line-numbers-mode" data-highlighter="prismjs" data-ext="console" data-title="console"><pre v-pre><code><span class="line">baygon --config other.yaml</span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div></div></div><p>Other names such as <code v-pre>t</code>, <code v-pre>test</code> or <code v-pre>tests</code> can be used, but the extension must be <code v-pre>.json</code>, <code v-pre>.yml</code> or <code v-pre>.yaml</code>. Here some valid configuration names:</p>
<div class="language-text line-numbers-mode" data-highlighter="prismjs" data-ext="text" data-title="text"><pre v-pre><code><span class="line">baygon.yml</span>
<span class="line">baygon.yaml</span>
<span class="line">baygon.json</span>
<span class="line">tests.yml</span>
<span class="line">t.json</span>
<span class="line">...</span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><h2 id="tests-of-strings" tabindex="-1"><a class="header-anchor" href="#tests-of-strings"><span>Tests of strings</span></a></h2>
<p>Baygon currently features three type of tests :</p>
<ul>
<li><code v-pre>contains</code>: A string contained into the corresponding output.</li>
<li><code v-pre>regex</code>: A Python regular expression</li>
<li><code v-pre>equals</code>: An exact match</li>
</ul>
<p>You can combine any of the three tests together:</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">stdout</span><span class="token punctuation">:</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">contains</span><span class="token punctuation">:</span> foo <span class="token comment"># Must contain the word foo</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">regex</span><span class="token punctuation">:</span> f(oo<span class="token punctuation">|</span>aa<span class="token punctuation">|</span>uu) <span class="token comment"># Must match</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">equals</span><span class="token punctuation">:</span> foobar</span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><p>You can also add a negation with the <code v-pre>not</code> keyword:</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">stdout</span><span class="token punctuation">:</span></span>
<span class="line">      <span class="token key atrule">not</span><span class="token punctuation">:</span></span>
<span class="line">        <span class="token punctuation">-</span> <span class="token key atrule">contains</span><span class="token punctuation">:</span> foo <span class="token comment"># Must contain the word foo</span></span>
<span class="line">        <span class="token punctuation">-</span> <span class="token key atrule">regex</span><span class="token punctuation">:</span> f(oo<span class="token punctuation">|</span>aa<span class="token punctuation">|</span>uu) <span class="token comment"># Must match</span></span>
<span class="line">        <span class="token punctuation">-</span> <span class="token key atrule">equals</span><span class="token punctuation">:</span> foobar</span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div></div></template>


