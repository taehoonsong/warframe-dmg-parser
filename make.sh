#/usr/bin/env bash

pyinstaller \
    --clean \
    --onefile \
    --windowed \
    --log-level=WARN \
    --icon=parser.ico \
    --name=warframe-dmg-parser \
    main.py