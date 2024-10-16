# SPA Extractor
A small tool written to help me extract particle textures from NSMB's `.SPA` (v22_1) particle files.

## Usage
Requires python to be installed and basic knowledge of the command line.

Usage: `spa-extract.py [-h] [-o OUTPUT_FOLDER] [-m] input_file`
* `input_file`: the `.spa` file to extract textures from, or a directory. If a directory is supplied, the progrma will attempt to extract textures from all `.spa` files within (non-recursively).  
* `-h`, `--help`: shows the help menu with descriptions of the available flags.
* `-o`, `--output`: changes the output directory of the extracted textures as `.png`s. Default: `.` (current directory)
* `-m`, `--apply-mirroring`: outputs the textures with proper horizontal/vertical mirroring. Might break some textures as they could have mirroring enabled, but don't use it in-game.
