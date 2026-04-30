css = """
/* Apple Emoji Style */
img.apple-emoji {
    width: 1.2em;
    height: 1.2em;
    vertical-align: -0.2em;
    display: inline-block;
    border: none;
    box-shadow: none;
    background: transparent;
}
"""
with open('frontend/css/style.css', 'a', encoding='utf-8') as f:
    f.write(css)
