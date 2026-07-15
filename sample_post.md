![](https://telegram.org/img/t_logo.png "Amethyst Post Bot")

# Amethyst Post Bot Format Showcase

This post demonstrates the formatting features supported by Amethyst Post Bot.

You can combine headings, bold text, spoilers, expandable sections, media collections, quotes, and mathematical formulas in a single post.

**All elements below are included for demonstration purposes.**

<aside>
Use an accent block to highlight an important announcement, warning, note, or quotation.
<cite>Amethyst Post Bot</cite>
</aside>

:::details What can I send to the bot?
You can send Markdown directly in a message or upload a UTF-8 encoded file with the `.md` extension.

:::details open What does an expanded block look like?
This section is displayed in its expanded state by default.

It can contain multiple paragraphs, **bold text**, ||spoilers||, links, and other supported formatting.
:::

## Image Collage

A collage displays several images together in a compact layout.

## Slideshow

A slideshow allows readers to browse multiple images one at a time.

## Spoilers

Spoilers can hide additional information until the reader opens it.

Example: ||this text is hidden by default||.

:::details Can local images be used?
No. Media links must begin with `http://` or `https://` so Telegram can download and process them.
:::

## Formula Rendering

The bot can also process complex mathematical expressions:

$$
\forall x \in \mathbb{R},\quad
F(x)=\sum_{n=1}^{\infty}\frac{(-1)^{n+1}x^{2n}}{n!}
+\int_{0}^{\pi}\sin(t),dt
-\prod_{k=1}^{m}(k+1)
+\sqrt{\frac{a^2+b^2}{c^2}}
\neq \varnothing,
\quad
\alpha+\beta-\gamma\cdot\delta\div\epsilon
\leq \zeta \geq \eta
\Rightarrow \theta \Leftrightarrow \lambda
$$

## End of the Demonstration

This example includes:

* headings and subheadings;
* bold text;
* accent blocks and citations;
* collapsed and expanded sections;
* image collages;
* slideshows;
* spoilers;
* mathematical formulas.
  :::
