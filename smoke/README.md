# V0.9 open movie smoke test

Two independent, static CMS-shaped JSON fixtures with open movie links. Import smoke.json in a multi-repository client; for single-repository clients import one of the group JSON files. Static raw files ignore query parameters: search is disabled, and clients may differ in how they handle category/detail requests. These are not production releases. Media remains on Google's public sample bucket, not GitHub.

- Big Buck Bunny (2008): © Blender Foundation / www.bigbuckbunny.org, [project and license](https://peach.blender.org/about/).
- Tears of Steel (2012): © Blender Foundation / mango.blender.org, [project](https://mango.blender.org/about/), [official release](https://www.youtube.com/watch?v=R6MlUcmOul8).
- Both films: [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). Linked sample copies; no media files redistributed.
- Sample URLs documented at https://gist.github.com/jsturgis/3b19447b304616f18657. Actual availability and decoding depend on the client/network.

The optional local test server provides real filtered category, list, detail and keyword responses using the same two records. No media proxy or external requests. See docs/TV-ACCEPTANCE.md.
