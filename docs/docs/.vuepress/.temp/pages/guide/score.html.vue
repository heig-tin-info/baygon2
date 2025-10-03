<template><div><h1 id="academic-assignment" tabindex="-1"><a class="header-anchor" href="#academic-assignment"><span>Academic Assignment</span></a></h1>
<p>Baygon is well designed to handle academic assignments. You can specify the points for each test, group of tests or at the top level.</p>
<p>The configuration keys you can use are:</p>
<p><strong><code v-pre>points</code></strong></p>
<p>The total points that can be earned from the whole suite, group of tests or test.</p>
<p><strong><code v-pre>weight</code></strong></p>
<p>The weight of a test or group of tests. The weight is used to calculate the available points. A default <code v-pre>weight</code> value of <code v-pre>10</code> is used but you can set it to any value you want according to your needs.</p>
<p><strong><code v-pre>min-points</code></strong></p>
<p>When using weights, for instance if you have a group of test awarded 2 points shared in three tests of equally weights, each test will be awarded 0.666...points. The <code v-pre>min-points</code> key allows you to set a minimum value for the points. In this case, if you set <code v-pre>min-points</code> to <code v-pre>1</code>, each test will be awarded 1 point. Typical values are <code v-pre>1</code>, <code v-pre>0.5</code>, <code v-pre>0.25</code> or <code v-pre>0.1</code>.</p>
<p>Baygon will automatically figure out how to assign points to each test based on your entries. Some rules apply:</p>
<ol>
<li>Without any other information each successfull test is awarded 1 points.</li>
<li>If a total number of points is specified at any level, the points are distributed equally among the subtests.</li>
<li>Weights can be used influence the distribution of points. The default weight is 10.</li>
</ol>
<p>To give you some examples we will simplify the configuration files.</p>
<h2 id="equally-distributed-points" tabindex="-1"><a class="header-anchor" href="#equally-distributed-points"><span>Equally distributed points</span></a></h2>
<p>By default we know that <code v-pre>min-points</code> is 0.1 and with equal <code v-pre>weight</code> on each test, the points are distributed equally.</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span></span>
<span class="line"><span class="token key atrule">points</span><span class="token punctuation">:</span> <span class="token number">10</span></span>
<span class="line"><span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test 1 <span class="token comment"># 3.4</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test 2 <span class="token comment"># 3.3</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test 3 <span class="token comment"># 3.3</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><h2 id="weighted-points-distribution" tabindex="-1"><a class="header-anchor" href="#weighted-points-distribution"><span>Weighted points distribution</span></a></h2>
<p>This time we have two subgroups of tests. The first group has a weight of 5 and the second group has a weight of 10. The total points are 10.</p>
<div class="language-yaml line-numbers-mode" data-highlighter="prismjs" data-ext="yml" data-title="yml"><pre v-pre><code><span class="line"><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span></span>
<span class="line"><span class="token key atrule">points</span><span class="token punctuation">:</span> <span class="token number">12</span></span>
<span class="line"><span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Group 1 <span class="token comment"># 4</span></span>
<span class="line">    <span class="token key atrule">weight</span><span class="token punctuation">:</span> <span class="token number">5</span></span>
<span class="line">    <span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test 1 <span class="token comment"># 2</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test 2 <span class="token comment"># 2</span></span>
<span class="line">  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Group 2 <span class="token comment"># 8</span></span>
<span class="line">    <span class="token key atrule">weight</span><span class="token punctuation">:</span> <span class="token number">10</span></span>
<span class="line">    <span class="token key atrule">tests</span><span class="token punctuation">:</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test 3 <span class="token comment"># 4</span></span>
<span class="line">      <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test 4 <span class="token comment"># 4</span></span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div><div class="line-number"></div></div></div><h2 id="using-the-result" tabindex="-1"><a class="header-anchor" href="#using-the-result"><span>Using the result</span></a></h2>
<p>The number of points is given on the output it has the form of:</p>
<div class="language-text line-numbers-mode" data-highlighter="prismjs" data-ext="text" data-title="text"><pre v-pre><code><span class="line">Points: 4/10</span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div></div></div><p>Alternatively you may want to use the report feature to generate a report in JSON or YAML format. The report will contain the points for each test and group of tests.</p>
<div class="language-console line-numbers-mode" data-highlighter="prismjs" data-ext="console" data-title="console"><pre v-pre><code><span class="line">baygon --report=report.json</span>
<span class="line"></span></code></pre>
<div class="line-numbers" aria-hidden="true" style="counter-reset:line-number 0"><div class="line-number"></div></div></div><p>This report could be used by a grading system to automatically assign grades to students.</p>
</div></template>


