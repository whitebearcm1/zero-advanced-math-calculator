# Calculus Calculator

A symbolic calculus calculator built with **Python + Tkinter + SymPy**.

## Features
- Derivatives (single & multivariable, higher order)
- Indefinite / definite / multiple integrals
- Critical points and Lagrange multipliers
- Automatic substitution and history

## How to Use (Windows)

1. Download the whole repository (or the `dist` folder contents).
2. **Keep `高数计算器.exe` and the `_internal` folder together.**
3. Double-click `高数计算器.exe` to run.

> ⚠️ **Important**: Do not move or delete the `_internal` folder.  
> It contains all required runtime files (Python DLLs, libraries, and the icon).  
> The program will not start without it.

## Requirements (for source)
pip install sympy

## Run from source
python main.py

## Build EXE
pyinstaller -F -w -i icon.ico --add-data "icon.ico;." -n CalculusCalculator main.py
