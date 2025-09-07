@echo off

pyinstaller ^
    --clean ^
    --onefile ^
    --windowed ^
    --log-level=WARN ^
    --icon=parser.ico ^
    --name=warframe-dmg-parser ^
    main.py