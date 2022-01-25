# AAXtoMPpy
This is an attempt to provide the functionality of 
https://github.com/KrumpetPirate/AAXtoMP3 through python.  
Currently supports conversion to mp3 file format with subsequent splitting into
chapters derived from file metadata. 

## Requirements
* ffmpeg findable by the default shell  
* Python 3.7 (probably works with some lower versions, but I don't know which
features came when...)  
* Your personal audible activation bytes. See
https://github.com/inAudible-NG/audible-activator or
https://github.com/inAudible-NG/tables on how you can obtain them.  
  
## Usage
This script now has command line options:

    -h, --help            show this help message and exit
      -i [INFILE [INFILE ...]], --infile [INFILE [INFILE ...]]
                            Input files, if given, the .aax files among them will be converted. If not given, an input dir has to be given with -d
      -d [DIRECTORY [DIRECTORY ...]], --directory [DIRECTORY [DIRECTORY ...]]
                            Directory/ies from which .aax files will be converted.
      -f FORMAT, --format FORMAT
                            Format abbreviation for the file format the input files will be converted to. See ffmpeg documentation on which ones are possible. Default: mp3
      -c CODEC, --codec CODEC
                            Encoder that ffmpeg should use, see their documentation on possible options.
      -b, --debug           Set logging level to debug.
      -a AUTHCODE, --authcode AUTHCODE
                            Personal audible activation code, see github page on how to obtain it. If not given, a '.authcode' file containing nothing but the activation
                            code needs to be in the current directory.
      -o OUTPUT, --output OUTPUT
                            Output directory path.

## Notes
Tested only on ``Ubuntu 20.04 LTS`` with python ``3.9`` and ffmpeg version
``4.2.4-1ubuntu0.1``.
