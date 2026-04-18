# Social preview image

## Specification

- Size: 1280 × 640 (GitHub social preview standard)
- Format: PNG
- Theme: dark terminal motif
- Typography: mono-family (JetBrains Mono, Fira Code, or Inconsolata)
- Palette: near-black background, terminal green for accents, white for main text

## Copy layout

**Top (large, white)**:
> jailbreak-bench

**Middle (medium, green mono)**:
> 45 patterns / 7 categories / 251 tests / 0 bypasses

**Bottom (small, light gray)**:
> Hermes Labs · MIT · github.com/roli-lpci/jailbreak-bench

## Pollinations.ai prompt (free generator)

URL template:
```
https://image.pollinations.ai/prompt/{prompt}?width=1280&height=640&nologo=true&seed=4517
```

Prompt:
```
Minimal dark terminal aesthetic, matte black background with faint green scan lines. Large white mono text "jailbreak-bench" centered near top. Medium terminal-green mono text below reading "45 patterns  /  7 categories  /  251 tests  /  0 bypasses". Tiny footer in light gray mono: "Hermes Labs  ·  MIT  ·  github.com/roli-lpci/jailbreak-bench". Flat 2D, no photography, no 3D, no gradients beyond a subtle vignette. Clean, professional, zero noise. Composition leaves negative space around the central block.
```

Full Pollinations URL (paste into a browser):

```
https://image.pollinations.ai/prompt/Minimal%20dark%20terminal%20aesthetic%2C%20matte%20black%20background%20with%20faint%20green%20scan%20lines.%20Large%20white%20mono%20text%20%22jailbreak-bench%22%20centered%20near%20top.%20Medium%20terminal-green%20mono%20text%20below%20reading%20%2245%20patterns%20%2F%207%20categories%20%2F%20251%20tests%20%2F%200%20bypasses%22.%20Tiny%20footer%20in%20light%20gray%20mono%3A%20%22Hermes%20Labs%20%C2%B7%20MIT%20%C2%B7%20github.com%2Froli-lpci%2Fjailbreak-bench%22.%20Flat%202D%2C%20no%20photography%2C%20no%203D%2C%20no%20gradients%20beyond%20a%20subtle%20vignette.%20Clean%2C%20professional%2C%20zero%20noise.?width=1280&height=640&nologo=true&seed=4517
```

## Backup: hand-crafted SVG

If Pollinations output is noisy, `social-preview.svg` in this directory is a deterministic fallback (coming - see ticket #1). Export to PNG with `rsvg-convert -w 1280 social-preview.svg > social-preview.png`.

## Where to upload

- GitHub repo → Settings → Social preview → Upload image
- Used automatically when the repo URL is shared on X, LinkedIn, Slack, Discord

## Iteration notes

If the generated image has unreadable text (common pitfall with Pollinations for text-heavy layouts), switch to a hand-drawn SVG approach - text rendering via an image model is unreliable for any layout with more than ~5 words.

Alternative generator fallbacks:
- Stable Diffusion local (if you want full control)
- Canva (manual, but guaranteed text fidelity)
- A 15-line Python script using PIL that draws the three text blocks on a solid-color background
