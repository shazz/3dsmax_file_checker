# 3dsmax_file_checker
A little python script to check if a 3ds max file is compatible with Homestyler

# requirements

 - python 3+
 - `7z.exe` from 7-zip (CLI from https://www.7-zip.org/ package)

# usage

 1. Copy `7z.exe` in the script directory
 1. Create a folder named `tmp` in the script directory
 1. Create a folder named `tobeanalyzed` anywhere in the script directory (can be sub folder)
 1. Copy your `.max` files in this `tobeanalyzed` folder
 1. Run the script: `python check_max.py`

# results

````
Analyzing: 3d-model.max
File is not interlaced
Objects: 10
Vertices: 5904
Faces: 11392
Textures expected: 1
 - vegetation_grass1.jpg
Renderer: Default Scanline Renderer
3ds max Version: 2016
Save version: 2013
deleting temp files in tmp/4db440f5-7b40-4bf9-9d8b-651b00ffca6d/
----------------------------------------------------------------
Analyzing: Decorative_panel_corona_max_2014.max
File is not interlaced
Objects: 2
Vertices: 24442
Faces: 24710
Textures expected: None
Renderer: Corona 1.5 (hotfix 2)
3ds max Version: 2017
Save version: 2014
deleting temp files in tmp/9190c4be-1771-450f-89d8-0d386e7350d4/
````
