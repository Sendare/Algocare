from pathlib import Path

css_path = Path("cbt-app/exam.css")
css = css_path.read_text()

# 1. Fix the palette height and make it scrollable
old_palette = ".exam-palette { background: #09090b; border-top: 4px solid #27272a; padding: 16px; flex-shrink: 0; }"
new_palette = """.exam-palette { 
    background: #09090b; 
    border-top: 4px solid #27272a; 
    padding: 16px; 
    flex-shrink: 0; 
    max-height: 35vh; /* Limits palette to 35% of screen height */
    overflow-y: auto; /* Allows scrolling inside the palette */
}"""
css = css.replace(old_palette, new_palette)

# 2. Make the palette header sticky so it stays visible while scrolling
old_header = ".palette-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-weight: 700; color: #fff; font-size: 0.9rem; }"
new_header = """.palette-header { 
    display: flex; 
    justify-content: space-between; 
    align-items: center; 
    margin-bottom: 12px; 
    font-weight: 700; 
    color: #fff; 
    font-size: 0.9rem; 
    position: sticky; 
    top: -16px; /* Offsets padding to stick perfectly to top */
    background: #09090b; 
    padding: 10px 0; 
    z-index: 10; 
}"""
css = css.replace(old_header, new_header)

css_path.write_text(css)
print("✅ Fixed palette layout in exam.css")
