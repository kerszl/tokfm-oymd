#!/usr/bin/python3
from pathlib import Path, PureWindowsPath

sciezka="jakis\\test\\pliki"
filename_= PureWindowsPath(sciezka)
filename = Path(filename_)

print (filename)
