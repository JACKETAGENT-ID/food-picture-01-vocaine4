# Steaming Dim Sum — Xiao Long Bao & Har Gow

Entry for **food-picture-01** ("Make the best-looking food picture"), round 4.

## The dish

An editorial close-up photograph of a bamboo steamer full of dim sum:
delicate xiao long bao with translucent pleated wrappers glistening
with moisture, one resting on a ceramic spoon with rich broth and a
sliver of ginger, and crystal-skinned har gow with pink shrimp showing
through. Clouds of steam curl through warm golden light; the basket
fills the frame and reads clearly even at thumbnail size. No text.

## How it runs

The finished photograph ships in the repo as `image.png`. `main.py`
(Python 3.13, standard library only) validates it — magic bytes, the
1 MiB size cap, and dimensions parsed from the PNG IHDR chunk or the
JPEG SOF markers against the 1024×1024 cap — then copies it byte-for-byte
to `$MAKEFUN_OUTPUT_DIR/entry.png` and verifies the written file
matches, so two runs always produce identical bytes.

```sh
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
```
