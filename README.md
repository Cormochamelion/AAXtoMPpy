# AAXtoMPpy
This is an attempt to provide the functionality of https://github.com/KrumpetPirate/AAXtoMP3 through python.  
Currently supports conversion to mp3 file format with subsequent splitting into chapters derived from file metadata. 

## Requirements
* ffmpeg findable by the default shell
* Python 3.7 (probably works with some lower versions, but I don't know which features came when...)
* Your personal audible activation bytes. See https://github.com/inAudible-NG/audible-activator or
 https://github.com/inAudible-NG/tables on how you can obtain them.

## Usage
* Place aax files to be converted into a folder called ``aax_input`` in the root directory of this repo
* Create a ```.authcode``` file in the root directory of this repo and write your authcode into it
 (just the characters obtained from the methods above in plain text).
* Run the script

Output files will be placed in the folder ``output`` within subdirectories according to Genre, Author, and Title. Metadata from the book is preserved
in the mp3 files.

## Notes
Tested only on windows 10 with python 3.7 and ffmpeg version git-2020-08-21-412d63f.
Currently there are no command line options. All aax files in the ``aax_input`` folder will get converted, 
the chapters split, and the original large mp3 file deleted afterwards. 
I probably won't work further on this because I got it to do what I want and can't be asked to invest much more time, 
but feel free to use and extend this script to your hearts content.
