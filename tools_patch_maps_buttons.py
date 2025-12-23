import re, sys, pathlib

p = pathlib.Path("bot.py")
s = p.read_text(encoding="utf-8")

def must(cond, msg):
    if not cond:
        print("PATCH FAILED:", msg)
        sys.exit(1)

orig = s

# 0) Ensure imports exist (safe no-op if already present)
if "InlineKeyboardButton" not in s or "InlineKeyboardMarkup" not in s:
    # Try to append to an existing telegram import line (common pattern)
    s2, n = re.subn(
        r"^from telegram import (.*)$",
        lambda m: m.group(0) if ("InlineKeyboardButton" in m.group(1) and "InlineKeyboardMarkup" in m.group(1))
        else f"from telegram import {m.group(1)}, InlineKeyboardButton, InlineKeyboardMarkup",
        s,
        flags=re.M
    )
    if n == 0:
        # Fallback: insert after first "from telegram import" block or near top
        lines = s.splitlines(True)
        inserted = False
        for i, line in enumerate(lines[:200]):
            if line.startswith("from telegram import "):
                lines.insert(i+1, "from telegram import InlineKeyboardButton, InlineKeyboardMarkup\n")
                inserted = True
                break
        must(inserted, "Could not find a suitable place to insert InlineKeyboard imports.")
        s = "".join(lines)
    else:
        s = s2

# 1) DETAILS VIEW: remove embedded maps URL line in parts.append(...), add button markup
# Remove any parts.append that embeds maps_url text
s, n_rm_details = re.subn(
    r'^\s*parts\.append\(\s*f"🗺️\s*\{maps_url\}"\s*\)\s*\n',
    "",
    s,
    flags=re.M
)

# Inject reply_markup into the details reply_text block where `msg = "\n".join(parts)` exists
# We look for the first occurrence in the "details" branch (it’s very distinctive).
pattern_details = re.compile(
    r'(msg\s*=\s*"\\n"\.join\(parts\)\s*\n\s*await update\.message\.reply_text\(\s*\n\s*msg,\s*\n)([\s\S]*?\n\s*\)\s*)',
    re.M
)
m = pattern_details.search(s)
must(m is not None, "Could not find details reply_text(msg, ...) block to patch.")

details_head = m.group(1)
details_tail = m.group(2)

# Add reply_markup line (language-sensitive label)
details_inject = (
    '                        btn_label = "🗺️ Abrir en Maps" if lang == "es" else "🗺️ Open in Maps"\n'
    '                        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(btn_label, url=maps_url)]]) if maps_url else None\n'
)

# Ensure reply_text has reply_markup param
if "reply_markup=" not in details_head + details_tail:
    details_head = details_head + '                            reply_markup=reply_markup,\n'

s = s[:m.start()] + details_inject + details_head + details_tail + s[m.end():]

# 2) NL PLACES LIST: remove embedded maps URL line in `part += f"\n🗺️ {maps_url}"` and add buttons list + reply_markup
# Remove the url line append in NL list loop
s, n_rm_list = re.subn(
    r'^\s*part\s*\+=\s*f"\\n🗺️\s*\{maps_url\}"\s*\n',
    "",
    s,
    flags=re.M
)

# Add buttons initialization right after `lines = []` inside NL places block (first match near that section)
s2, n_buttons_init = re.subn(
    r'(lines\s*=\s*\[\]\s*\n)',
    r'\1        buttons = []\n',
    s,
    count=1
)
must(n_buttons_init == 1, "Could not insert buttons = [] after lines = [] in NL places section.")
s = s2

# After each lines.append(part), add a button if maps_url exists (first match only, within NL places loop)
s2, n_add_button = re.subn(
    r'(lines\.append\(part\)\s*\n)',
    r'\1            if maps_url:\n                buttons.append([InlineKeyboardButton(f"🗺️ {i}", url=maps_url)])\n',
    s,
    count=1
)
must(n_add_button == 1, "Could not attach buttons.append(...) after lines.append(part) in NL places loop.")
s = s2

# Add reply_markup to the NL list reply_text call (the one that sends header + join(lines) + footer)
pattern_list_reply = re.compile(
    r'(await update\.message\.reply_text\(\s*\n\s*header \+ "\\n\\n" \+ "\\n\\n"\.join\(lines\) \+ footer,\s*\n)([\s\S]*?\n\s*\)\s*)',
    re.M
)
m2 = pattern_list_reply.search(s)
must(m2 is not None, "Could not find NL list reply_text(header + join(lines) + footer, ...) block.")

list_head = m2.group(1)
list_tail = m2.group(2)

# Insert reply_markup computation before reply_text
list_inject = (
    '        reply_markup = InlineKeyboardMarkup(buttons) if buttons else None\n'
)

# Ensure reply_text includes reply_markup param
if "reply_markup=" not in list_head + list_tail:
    list_head = list_head + '            reply_markup=reply_markup,\n'

s = s[:m2.start()] + list_inject + list_head + list_tail + s[m2.end():]

# 3) Sanity: we expect at least one of the removals to have happened, otherwise patch likely missed the right code.
must((n_rm_details + n_rm_list) >= 1, "Did not remove any embedded maps_url lines; patterns likely mismatched.")

p.write_text(s, encoding="utf-8")

print("OK: patch applied",
      f"(removed detail url lines={n_rm_details}, removed list url lines={n_rm_list}, buttons_init={n_buttons_init}, add_button={n_add_button})")
