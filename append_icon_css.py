css = """
/* Phosphor Emoji Icon alignment */
i.emoji-icon {
    font-size: 1.25em;
    vertical-align: -0.15em;
    display: inline-block;
    line-height: 1;
}
"""
with open('frontend/css/style.css', 'a', encoding='utf-8') as f:
    f.write(css)
