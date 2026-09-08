This folder needs one font file for Hindi text to render correctly in
the generated PDF reports:

  NotoSansDevanagari-Regular.ttf

Where to get it:
  Search "Noto Sans Devanagari" (a free Google font family) and
  download the Regular weight as a .ttf file. Place it directly in
  this folder, next to this README.

Optional (improves English/Latin text rendering in the PDF too):
  NotoSans-Regular.ttf

If NotoSansDevanagari-Regular.ttf is missing, the app still runs and
still generates PDFs, but Hindi reports will not render Devanagari
script correctly - the app will show a warning on-screen in that case.

This is a one-time setup step done while you still have internet
(to download the font). Once the file is in this folder, PDF
generation works fully offline, every time, forever.
