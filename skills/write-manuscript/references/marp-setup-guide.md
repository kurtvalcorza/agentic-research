# Marp CLI Setup Guide

## Overview

**Marp CLI** is a command-line tool that converts Markdown files (with special Marp syntax) into presentation formats (PDF, PPTX, HTML). Write Manuscript Slide Deck uses Marp CLI for Phase 4 (Production) to export decks.

**Required for:** PDF and PPTX export
**Optional for:** HTML export (works without Marp CLI, just less optimized)

---

## Quick Start (TL;DR)

```bash
# Verify Node.js is installed (v16+ required)
node --version

# Use Marp CLI via npx (no global install needed)
npx @marp-team/marp-cli@latest presentation.md -o presentation.pdf

# If Node.js is not installed:
# Download from https://nodejs.org/ (LTS version)
```

**Recommended:** Keep Node.js updated to LTS version for best compatibility.

---

## Prerequisites

### 1. Node.js Installation

**Why needed:** Marp CLI is a Node.js package (runs on Node.js runtime).

**Check if installed:**
```bash
node --version
```

**Expected output:**
```
v20.10.0  # (or v16+, v18+, v20+)
```

**If not installed:**
1. Visit [nodejs.org](https://nodejs.org/)
2. Download the **LTS (Long Term Support)** version
   - Windows: `.msi` installer (64-bit)
   - macOS: `.pkg` installer (Apple Silicon or Intel)
   - Linux: Use package manager (see below)

**Installation by platform:**

#### Windows
```powershell
# Download installer from https://nodejs.org/
# Run the .msi file
# Verify installation:
node --version
npm --version
```

#### macOS
```bash
# Option 1: Official installer from https://nodejs.org/
# Download .pkg, run installer

# Option 2: Homebrew (if installed)
brew install node

# Verify:
node --version
```

#### Linux (Ubuntu/Debian)
```bash
# Using NodeSource repository (recommended)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify:
node --version
```

#### Linux (Fedora/RHEL)
```bash
sudo dnf install nodejs
```

---

### 2. npx (Node Package Executor)

**What it is:** Bundled with Node.js (v8.2+), runs npm packages without global installation.

**Check if available:**
```bash
npx --version
```

**If not available:** Update Node.js to v16+ (npx is built-in).

---

## Marp CLI Usage

### Basic Commands

**Generate PDF:**
```bash
npx @marp-team/marp-cli@latest presentation.md -o presentation.pdf
```

**Generate PPTX (PowerPoint):**
```bash
npx @marp-team/marp-cli@latest presentation.md --pptx -o presentation.pptx
```

**Generate HTML:**
```bash
npx @marp-team/marp-cli@latest presentation.md -o presentation.html
```

**Watch mode (auto-regenerate on file change):**
```bash
npx @marp-team/marp-cli@latest presentation.md -o presentation.pdf --watch
```

---

### Advanced Options

**Custom theme:**
```bash
npx @marp-team/marp-cli@latest presentation.md -o presentation.pdf --theme custom-theme.css
```

**PDF with speaker notes:**
```bash
npx @marp-team/marp-cli@latest presentation.md -o presentation.pdf --pdf-notes
```

**Export multiple formats at once:**
```bash
npx @marp-team/marp-cli@latest presentation.md -o output --pdf --pptx --html
# Creates: output.pdf, output.pptx, output.html
```

**Change PDF page size:**
```bash
# Default is 4:3 aspect ratio
# For 16:9:
npx @marp-team/marp-cli@latest presentation.md -o presentation.pdf --pdf-size 16:9

# For A4:
npx @marp-team/marp-cli@latest presentation.md -o presentation.pdf --pdf-size A4
```

---

## Troubleshooting

### Issue 1: "Command not found: npx"

**Cause:** Node.js is not installed, or PATH is not configured.

**Solution:**
1. Verify Node.js installation:
   ```bash
   node --version
   ```
2. If installed but npx not found, reinstall Node.js from [nodejs.org](https://nodejs.org/)
3. Restart terminal/command prompt after installation

---

### Issue 2: "Cannot find module '@marp-team/marp-cli'"

**Cause:** Network issue during package download, or npm cache corruption.

**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Retry command
npx @marp-team/marp-cli@latest presentation.md -o presentation.pdf
```

---

### Issue 3: PDF generation hangs or fails

**Cause:** Chromium (used by Marp for PDF rendering) may not be installed or accessible.

**Solution:**

**Windows:**
```powershell
# Ensure you have latest Node.js (v20+)
# Marp CLI auto-downloads Chromium on first run

# If still failing, manually install Chromium:
npx @puppeteer/browsers install chrome@stable
```

**macOS:**
```bash
# Same as Windows—Marp auto-downloads Chromium
# If failing, check macOS security settings:
# System Preferences → Security & Privacy → Allow apps downloaded from: App Store and identified developers
```

**Linux:**
```bash
# Install Chromium system-wide
sudo apt-get install chromium-browser  # Ubuntu/Debian
sudo dnf install chromium              # Fedora

# Or let Marp download it:
npx @marp-team/marp-cli@latest --version  # Triggers Chromium download
```

---

### Issue 4: "Error: EACCES: permission denied"

**Cause:** Insufficient permissions to write output file.

**Solution:**
```bash
# Check file permissions
ls -l presentation.pdf

# If file is read-only, remove it:
rm presentation.pdf

# Or change output directory:
npx @marp-team/marp-cli@latest presentation.md -o ~/Desktop/presentation.pdf
```

---

### Issue 5: Slow performance (large PDFs)

**Cause:** Many slides, high-resolution images, or complex CSS.

**Solution:**
1. **Optimize images:**
   - Compress images before embedding (use tools like `imagemagick`, `tinypng.com`)
   - Target: <500KB per image

2. **Simplify CSS:**
   - Remove unused styles
   - Avoid heavy animations

3. **Split deck:**
   - Break into multiple smaller Markdown files
   - Generate separate PDFs, combine later (e.g., `pdftk`)

---

### Issue 6: Fonts not rendering correctly in PDF

**Cause:** Custom fonts not embedded, or font files missing.

**Solution:**

**If using custom fonts in Marp:**
```css
/* In your Marp Markdown frontmatter */
---
marp: true
style: |
  @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
  section {
    font-family: 'Roboto', sans-serif;
  }
---
```

**Or use local fonts:**
```css
@font-face {
  font-family: 'MyFont';
  src: url('path/to/font.woff2') format('woff2');
}
section {
  font-family: 'MyFont', sans-serif;
}
```

**For system fonts:** Ensure the font is installed on the machine running Marp CLI.

---

## Alternative: Obsidian Plugins (No Marp CLI Needed)

If you prefer not to use Marp CLI, you can export decks directly from Obsidian using plugins:

### 1. Advanced Slides Plugin

**Install:**
1. Obsidian → Settings → Community Plugins → Browse
2. Search: "Advanced Slides"
3. Install + Enable

**Usage:**
- Write slides in Markdown (similar to Marp syntax)
- Click "Open as Slides" button
- Export to PDF from browser (Ctrl+P / Cmd+P → Print to PDF)

**Pros:** No CLI needed, visual preview
**Cons:** Less automation, manual export

---

### 2. Marp Slides Plugin (Obsidian)

**Install:**
1. Obsidian → Settings → Community Plugins → Browse
2. Search: "Marp Slides"
3. Install + Enable

**Usage:**
- Write Marp-formatted Markdown in Obsidian
- Right-click file → "Export Marp Slide to PDF"

**Pros:** Integrates Marp into Obsidian
**Cons:** Still requires Marp CLI in background (auto-installed by plugin)

---

## HTML Export (No CLI Fallback)

If Marp CLI is not available, Write Manuscript Slide Deck can generate HTML output directly:

**Manual conversion:**
1. Copy `presentation.md` content
2. Use online Marp editor: [marp.app](https://marp.app/)
3. Paste content → Preview → Download HTML
4. Open HTML in browser → Print to PDF (Ctrl+P / Cmd+P)

**Quality:** Lower than Marp CLI PDF (browser rendering differences), but functional.

---

## Best Practices

### 1. Use `npx` (Not Global Install)

**Why:**
- Always uses latest version (`@latest`)
- No global package management (cleaner)
- Works across different projects without version conflicts

**Avoid:**
```bash
npm install -g @marp-team/marp-cli  # Global install (not recommended)
```

**Prefer:**
```bash
npx @marp-team/marp-cli@latest ...  # Always latest, no install
```

---

### 2. Version Pin for Production

If you need reproducible builds (e.g., CI/CD):

```bash
# Install specific version locally
npm install --save-dev @marp-team/marp-cli@3.4.0

# Use in package.json script
{
  "scripts": {
    "build-slides": "marp presentation.md -o presentation.pdf"
  }
}

# Run via npm
npm run build-slides
```

---

### 3. Automate with Scripts

**Bash script (Linux/macOS):**
```bash
#!/bin/bash
# build-deck.sh

MARKDOWN_FILE="presentation.md"
OUTPUT_DIR="output"

mkdir -p "$OUTPUT_DIR"

echo "Building PDF..."
npx @marp-team/marp-cli@latest "$MARKDOWN_FILE" -o "$OUTPUT_DIR/presentation.pdf"

echo "Building PPTX..."
npx @marp-team/marp-cli@latest "$MARKDOWN_FILE" --pptx -o "$OUTPUT_DIR/presentation.pptx"

echo "Building HTML..."
npx @marp-team/marp-cli@latest "$MARKDOWN_FILE" -o "$OUTPUT_DIR/presentation.html"

echo "Done! Files in $OUTPUT_DIR/"
```

**PowerShell script (Windows):**
```powershell
# build-deck.ps1

$MarkdownFile = "presentation.md"
$OutputDir = "output"

New-Item -ItemType Directory -Force -Path $OutputDir

Write-Host "Building PDF..."
npx @marp-team/marp-cli@latest $MarkdownFile -o "$OutputDir\presentation.pdf"

Write-Host "Building PPTX..."
npx @marp-team/marp-cli@latest $MarkdownFile --pptx -o "$OutputDir\presentation.pptx"

Write-Host "Building HTML..."
npx @marp-team/marp-cli@latest $MarkdownFile -o "$OutputDir\presentation.html"

Write-Host "Done! Files in $OutputDir\"
```

---

## CI/CD Integration (GitHub Actions)

**Automate deck generation on commit:**

```yaml
# .github/workflows/build-slides.yml

name: Build Slides

on:
  push:
    paths:
      - 'presentation.md'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Build PDF
        run: npx @marp-team/marp-cli@latest presentation.md -o presentation.pdf

      - name: Upload PDF artifact
        uses: actions/upload-artifact@v3
        with:
          name: slides
          path: presentation.pdf
```

**Result:** Every commit to `presentation.md` auto-generates PDF (downloadable from GitHub Actions artifacts).

---

## Performance Tips

### 1. Cache Chromium Download

**Problem:** Marp downloads Chromium (~200MB) on first run.

**Solution (CI/CD):**
```yaml
# Cache Chromium across builds
- name: Cache Chromium
  uses: actions/cache@v3
  with:
    path: ~/.cache/puppeteer
    key: chromium-${{ runner.os }}
```

---

### 2. Parallel Builds

If generating multiple decks:

```bash
# Sequential (slow)
npx @marp-team/marp-cli@latest deck1.md -o deck1.pdf
npx @marp-team/marp-cli@latest deck2.md -o deck2.pdf
npx @marp-team/marp-cli@latest deck3.md -o deck3.pdf

# Parallel (fast)
npx @marp-team/marp-cli@latest deck1.md -o deck1.pdf &
npx @marp-team/marp-cli@latest deck2.md -o deck2.pdf &
npx @marp-team/marp-cli@latest deck3.md -o deck3.pdf &
wait  # Wait for all background jobs
```

---

## Security Considerations

### 1. Untrusted Markdown

**Risk:** Marp Markdown can include HTML/CSS, potentially malicious scripts.

**Mitigation:**
- Only render trusted Markdown files
- Avoid copy-pasting Markdown from untrusted sources
- Marp CLI sanitizes scripts by default (but not foolproof)

---

### 2. Network Requests in Markdown

**Risk:** Markdown can load external resources (images, fonts, CSS from URLs).

**Mitigation:**
- Use local assets when possible
- Review external URLs before rendering
- Use `--allow-local-files` flag cautiously (restricts file:// access)

---

## Further Resources

**Official Documentation:**
- Marp CLI: [github.com/marp-team/marp-cli](https://github.com/marp-team/marp-cli)
- Marp Syntax: [marpit.marp.app](https://marpit.marp.app/)
- Themes: [github.com/marp-team/marp-core/tree/main/themes](https://github.com/marp-team/marp-core/tree/main/themes)

**Community:**
- Discussions: [github.com/marp-team/marp/discussions](https://github.com/marp-team/marp/discussions)
- Examples: [github.com/yhatt/marp/wiki/Marp-examples](https://github.com/yhatt/marp/wiki/Marp-examples)

**Related Tools:**
- Reveal.js: Alternative Markdown slide framework (more interactive)
- Slidev: Vue-based slide framework (developer-focused)
- Obsidian Advanced Slides: Obsidian-native solution

---

## Related Documentation

- **[[../SKILL.md]]** - Write Manuscript Slide Deck technical implementation
- **[[../README.md]]** - User guide
- **[[scipab-framework.md]]** - SCIPAB storytelling framework
- **[[../templates/scipab-academic.md]]** - Academic template
- **[[../templates/scipab-executive.md]]** - Executive template
- **[[../templates/scipab-technical.md]]** - Technical template

