# Cinematic site generator

`pages/cinematic/**` is generated. Edit copy here, never in the HTML.

```bash
python3 tools/cinematic/gen.py        # EN pages from frag/ + merge_frag.py + georgeai_services.json + pages/pricing
python3 tools/cinematic/translate.py  # de/ fr/ ro/ ar/ from the EN pages via de.py, fr.py, ro.py, ar.py
./deploy.sh --no-content              # ship
```

A string missing from a dictionary stays English; `translate.py` prints what is untranslated.
