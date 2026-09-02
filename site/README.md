# Proposal site

The revised proposal as a single HTML page, `index.html`. No build step and no
dependencies beyond Google Fonts.

To view it, open `site/index.html` in a browser, or serve the folder:

```bash
python3 -m http.server 8080 -d site
```

Then open http://localhost:8080. The page is print-styled: File > Print produces a
paginated letter-size PDF with a cover, contents, and one section per page.

To publish, drag the `site/` folder onto Netlify, or point any static host at it.
