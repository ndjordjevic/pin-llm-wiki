"""Render frames of an animated terminal-style demo, then assemble into a GIF."""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ---------- Layout & palette ----------
W, H = 920, 780
BG          = (250, 250, 252)
PANEL_BG    = (255, 255, 255)
TITLE_GRAY  = (140, 140, 150)
SUBTLE_GRAY = (185, 185, 195)
DIVIDER     = (228, 228, 235)
ORANGE      = (235, 114, 60)        # heading + command echo
GREEN       = (74, 162, 92)         # success
ARROW_ORANGE= (235, 130, 60)        # progress arrow
INSTALL_BG  = (232, 250, 235)
INSTALL_BD  = (158, 213, 167)
TAB_BD_RED  = (235, 114, 60)
TAB_BD_BLUE = (110, 138, 220)
TAB_BD_PURP = (171, 138, 200)
PROMPT_GRAY = (185, 185, 195)
DOT_RED     = (236, 105, 95)
DOT_YEL     = (245, 192, 79)
DOT_GRN     = (98, 197, 87)

FONT_SANS_PATH = "/System/Library/Fonts/SFNS.ttf"          # SF Pro
FONT_MONO_PATH = "/System/Library/Fonts/SFNSMono.ttf"      # SF Mono — also covers ✓ → ●
FONT_SYM_PATH  = FONT_MONO_PATH

def font(size: int, hand: bool = True) -> ImageFont.FreeTypeFont:
    # `hand` kept for call-site compatibility: True == sans (UI), False == mono (terminal)
    return ImageFont.truetype(FONT_SANS_PATH if hand else FONT_MONO_PATH, size)

def sym_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_SYM_PATH, size)

def mono(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_MONO_PATH, size)


# ---------- Animation script ----------
@dataclass
class OutputLine:
    text: str
    color: tuple
    indent: int = 0          # extra x offset (pixels)
    gap_above: int = 0       # vertical gap before this line


@dataclass
class Step:
    cmd: str                 # text to type after the ">" prompt
    outputs: list[OutputLine] = field(default_factory=list)
    type_cps: int = 28       # chars-per-frame batch (effectively typing speed)
    pause_after_cmd: int = 6 # frames to pause after command finished typing
    pause_after_out: int = 12


STEPS: list[Step] = [
    Step(
        cmd="/pin-llm-wiki init",
        outputs=[
            OutputLine("Scaffolded wiki structure in ./my-wiki", GREEN),
            OutputLine("inbox.md   .pin-llm-wiki.yml   AGENTS.md", GREEN, indent=22),
            OutputLine("wiki/   raw/", GREEN, indent=22),
        ],
    ),
    Step(
        cmd="/pin-llm-wiki queue https://github.com/langchain-ai/langgraph",
        outputs=[
            OutputLine("Queued 1 URL -> inbox.md   1 item pending", GREEN),
        ],
    ),
    Step(
        cmd="/pin-llm-wiki ingest",
        outputs=[
            OutputLine("Fetching GitHub: langchain-ai/langgraph ...", ARROW_ORANGE, gap_above=2),
            OutputLine("raw/github/langchain-ai-langgraph.md  (284 KB)", GREEN),
            OutputLine("Generating wiki pages ...", ARROW_ORANGE),
            OutputLine("wiki/sources/langgraph.md  (created)", GREEN),
            OutputLine("wiki/overview.md  (updated)   wiki/log.md  (appended)", GREEN),
        ],
    ),
    Step(
        cmd="/pin-llm-wiki ingest https://youtu.be/zjkBMFhNj_g",
        outputs=[
            OutputLine("yt-dlp: extracting transcript and chapters ...", ARROW_ORANGE),
            OutputLine("raw/youtube/zjkbmfhnj_g-attention-is-all-you-need.md", GREEN),
            OutputLine("wiki/sources/attention-is-all-you-need.md  (created)", GREEN),
        ],
    ),
    Step(
        cmd="/pin-llm-wiki lint",
        outputs=[
            OutputLine("2 sources   0 broken links   wiki is healthy", GREEN),
        ],
    ),
    # Final step: query the wiki
    Step(
        cmd='/pin-llm-wiki ask "how does langgraph compare to the transformer paper?"',
        outputs=[
            OutputLine("Searching wiki/  ... 2 sources matched", ARROW_ORANGE),
            OutputLine("LangGraph -> stateful agent graphs over LLM nodes (langgraph.md)", GREEN),
            OutputLine("Transformer -> attention-only seq2seq architecture (attention-...md)", GREEN),
            OutputLine("Drafted answer in wiki/answers/langgraph-vs-transformer.md", GREEN),
        ],
        pause_after_out=40,    # final hold
    ),
]


# ---------- Rendering primitives ----------
def round_rect(d: ImageDraw.ImageDraw, box, radius, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def base_canvas() -> tuple[Image.Image, dict]:
    """Render the static parts of the page once. Returns (image, layout)."""
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    # outer panel with subtle shadow
    panel = (28, 24, W - 28, H - 24)
    round_rect(d, (panel[0]+3, panel[1]+5, panel[2]+3, panel[3]+5), 18, fill=(238, 238, 244))
    round_rect(d, panel, 18, fill=PANEL_BG, outline=DIVIDER, width=1)

    # title bar
    bar_h = 44
    bar = (panel[0], panel[1], panel[2], panel[1] + bar_h)
    # top corners rounded by reusing the panel rounding
    d.line((panel[0]+1, bar[3], panel[2]-1, bar[3]), fill=DIVIDER)
    # traffic lights
    cy = bar[1] + bar_h // 2
    for i, c in enumerate((DOT_RED, DOT_YEL, DOT_GRN)):
        cx = bar[0] + 22 + i * 18
        d.ellipse((cx-6, cy-6, cx+6, cy+6), fill=c)
    # title
    title = "Claude Code  ·  pin-llm-wiki"
    f_title = font(20, hand=True)
    tw = d.textlength(title, font=f_title)
    d.text((panel[0] + (panel[2]-panel[0]-tw)/2, bar[1] + 11), title, fill=ORANGE, font=f_title)

    # tab strip
    tabs_y = bar[3] + 6
    tab_h = 36
    tab_w = (panel[2] - panel[0] - 40) / 3
    tab_specs = [
        ("✦", "Claude Code",    TAB_BD_RED,  True),
        ("+", "GitHub Copilot", TAB_BD_BLUE, False),
        ("○", "Cursor",         TAB_BD_PURP, False),
    ]
    f_tab  = font(18, hand=True)
    f_tabs = sym_font(16)
    for i, (sym, label, color, active) in enumerate(tab_specs):
        x0 = panel[0] + 20 + i * tab_w
        box = (x0, tabs_y, x0 + tab_w - 14, tabs_y + tab_h)
        if active:
            round_rect(d, box, 6, fill=PANEL_BG, outline=color, width=2)
            text_color = ORANGE
        else:
            round_rect(d, box, 6, fill=PANEL_BG, outline=DIVIDER, width=1)
            text_color = SUBTLE_GRAY
        sw = d.textlength(sym, font=f_tabs)
        lw = d.textlength(label, font=f_tab)
        total = sw + 8 + lw
        sx = box[0] + (box[2]-box[0]-total)/2
        d.text((sx, box[1] + 9), sym, fill=text_color, font=f_tabs)
        d.text((sx + sw + 8, box[1] + 7), label, fill=text_color, font=f_tab)

    # heading
    head_y = tabs_y + tab_h + 22
    f_head = font(24, hand=True)
    d.ellipse((panel[0]+30, head_y+10, panel[0]+44, head_y+24), fill=ORANGE)
    d.text((panel[0]+54, head_y), "Claude Code", fill=ORANGE, font=f_head)
    f_sub = font(16, hand=True)
    d.text((panel[0]+54, head_y + 32),
           "pin-llm-wiki  ·  Karpathy LLM Wiki pattern as a skill",
           fill=TITLE_GRAY, font=f_sub)

    # install box (step 1) — already complete
    box_top = head_y + 70
    box = (panel[0]+30, box_top, panel[2]-30, box_top + 78)
    round_rect(d, box, 8, fill=INSTALL_BG, outline=INSTALL_BD, width=2)
    f_step  = font(14, hand=True)
    f_sym   = sym_font(13)
    f_cmd_m = mono(14)
    f_csym  = sym_font(15)
    d.text((box[0]+16, box[1]+8), "1.", fill=GREEN, font=f_sym)
    d.text((box[0]+38, box[1]+8), "Install", fill=GREEN, font=f_step)
    d.text((box[0]+16, box[1]+28), ">  npx skills@latest add ndjordjevic/pin-llm-wiki",
           fill=ORANGE, font=f_cmd_m)
    d.text((box[0]+16, box[1]+50), "✓", fill=GREEN, font=f_csym)
    d.text((box[0]+38, box[1]+50),
           "pin-llm-wiki installed  ·  use /pin-llm-wiki in Claude Code, Copilot, or Cursor",
           fill=GREEN, font=f_cmd_m)

    # "Use in Claude Code" subhead
    sub_y = box[3] + 18
    d.line((panel[0]+30, sub_y-6, panel[2]-30, sub_y-6), fill=DIVIDER)
    d.text((panel[0]+30, sub_y), "2.", fill=TITLE_GRAY, font=f_sym)
    d.text((panel[0]+52, sub_y), "Use in Claude Code", fill=TITLE_GRAY, font=f_step)

    # footer
    footer_y = H - 78
    d.line((panel[0]+30, footer_y-12, panel[2]-30, footer_y-12), fill=DIVIDER)
    f_foot  = font(15, hand=True)
    f_fsym  = sym_font(14)
    d.text((panel[0]+30, footer_y), "Same commands work in:", fill=TITLE_GRAY, font=f_foot)
    # buttons
    bx = panel[0]+220
    btn1 = (bx, footer_y-6, bx+180, footer_y+24)
    round_rect(d, btn1, 6, fill=PANEL_BG, outline=TAB_BD_BLUE, width=2)
    d.text((btn1[0]+12, btn1[1]+7), "+", fill=TAB_BD_BLUE, font=f_fsym)
    d.text((btn1[0]+28, btn1[1]+5), "VS Code + Copilot", fill=TAB_BD_BLUE, font=f_foot)
    btn2 = (btn1[2]+14, btn1[1], btn1[2]+14+120, btn1[3])
    round_rect(d, btn2, 6, fill=PANEL_BG, outline=TAB_BD_PURP, width=2)
    d.text((btn2[0]+12, btn2[1]+7), "○", fill=TAB_BD_PURP, font=f_fsym)
    d.text((btn2[0]+28, btn2[1]+5), "Cursor", fill=TAB_BD_PURP, font=f_foot)

    # area where commands stream
    layout = {
        "stream_left":  panel[0] + 30,
        "stream_top":   sub_y + 22,
        "stream_right": panel[2] - 30,
        "stream_bot":   footer_y - 22,
    }
    return im, layout


def draw_stream(base: Image.Image, layout: dict, completed_steps, current):
    """Render base + completed history + current partially-typed command,
    scrolling older lines off the top when the stream area overflows."""
    im = base.copy()
    d = ImageDraw.Draw(im)
    f_cmd  = mono(14)       # SF Mono for command line
    f_out  = mono(13)       # SF Mono for outputs
    f_psym = sym_font(14)   # ✓ → glyphs

    x = layout["stream_left"]
    y_top = layout["stream_top"]
    y_bot = layout["stream_bot"]
    avail = y_bot - y_top
    line_h = 22

    # entries: list of (kind, height, draw_fn). kind is "line" or "gap".
    entries: list[tuple[str, int, callable]] = []

    def add_command(text, with_caret):
        def fn(yy):
            d.text((x, yy), ">", fill=PROMPT_GRAY, font=f_cmd)
            d.text((x + 18, yy), " " + text, fill=ORANGE, font=f_cmd)
            if with_caret:
                cx = x + 18 + d.textlength(" " + text, font=f_cmd)
                d.rectangle((cx+1, yy+2, cx+9, yy+22), fill=(120,120,130))
        entries.append(("line", line_h, fn))

    def add_output(ol: OutputLine):
        def fn(yy):
            sym = "→" if ol.color == ARROW_ORANGE else "✓"
            d.text((x + 4, yy+1), sym, fill=ol.color, font=f_psym)
            d.text((x + 26 + ol.indent, yy), ol.text, fill=ol.color, font=f_out)
        if ol.gap_above:
            entries.append(("gap", ol.gap_above, lambda yy: None))
        entries.append(("line", line_h, fn))

    def add_gap(px):
        entries.append(("gap", px, lambda yy: None))

    for st, shown in completed_steps:
        add_command(st.cmd, with_caret=False)
        for ol in shown:
            add_output(ol)
        add_gap(6)

    if current is not None:
        partial, show_caret, shown_outputs = current
        add_command(partial, with_caret=show_caret)
        for ol in shown_outputs:
            add_output(ol)

    total = sum(h for _, h, _ in entries)
    if total > avail:
        # Drop from the top until the remainder fits.
        cut = 0
        running = total
        while cut < len(entries) and running > avail:
            running -= entries[cut][1]
            cut += 1
        entries = entries[cut:]

    y = y_top
    for kind, h, fn in entries:
        if kind == "gap":
            y += h
        else:
            fn(y)
            y += h

    return im


# ---------- Frame orchestration ----------
def build_frames(out_dir: Path) -> int:
    base, layout = base_canvas()
    completed: list[tuple[Step, list[OutputLine]]] = []
    frame_idx = 0

    def save(img):
        nonlocal frame_idx
        img.save(out_dir / f"frame_{frame_idx:04d}.png", optimize=False)
        frame_idx += 1

    # opening hold
    for _ in range(8):
        save(draw_stream(base, layout, completed, ("", True, [])))

    for s_i, step in enumerate(STEPS):
        # type the command
        partial = ""
        chars = list(step.cmd)
        i = 0
        while i < len(chars):
            # batch a few chars per frame so longer commands don't take forever
            batch = 1 if len(chars) <= 24 else 2
            partial += "".join(chars[i:i+batch])
            i += batch
            caret_blink = (frame_idx // 2) % 2 == 0
            save(draw_stream(base, layout, completed, (partial, True, [])))

        # pause with caret blink
        for k in range(step.pause_after_cmd):
            save(draw_stream(base, layout, completed, (partial, k % 4 < 2, [])))

        # reveal outputs progressively
        shown_outputs: list[OutputLine] = []
        for ol in step.outputs:
            shown_outputs.append(ol)
            for _ in range(3):
                save(draw_stream(base, layout, completed, (partial, False, shown_outputs)))

        # commit to history; brief settle
        completed.append((step, list(shown_outputs)))
        for _ in range(step.pause_after_out):
            save(draw_stream(base, layout, completed, ("", (frame_idx//2)%2==0, [])))

    # final long hold
    for _ in range(30):
        save(draw_stream(base, layout, completed, ("", (frame_idx//3)%2==0, [])))

    return frame_idx


def assemble_gif(frames_dir: Path, out_path: Path, fps: int = 12):
    palette = frames_dir / "palette.png"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-vf", "palettegen=stats_mode=diff",
        str(palette),
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-i", str(palette),
        "-lavfi", "paletteuse=dither=bayer:bayer_scale=5",
        "-loop", "0",
        str(out_path),
    ], check=True)


def main():
    here = Path(__file__).resolve().parent
    frames_dir = here / ".gif_frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir()
    n = build_frames(frames_dir)
    print(f"rendered {n} frames")
    out = here / "pin-llm-wiki-ai-cli-light.gif"
    assemble_gif(frames_dir, out, fps=14)
    size_kb = out.stat().st_size / 1024
    print(f"wrote {out}  ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
