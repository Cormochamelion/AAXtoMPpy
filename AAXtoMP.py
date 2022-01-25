#!/usr/bin/python3

import os
import sys
import pathlib
import re
import logging
import subprocess
import shutil
import argparse


def sanitize(string, replacement_symbol = "_"):
    """ 
    Turns filesystem-unfriendly characters into whatever is 
    specified by replacement_symbol (Default: "_") 
    """

    replace_dict = {" ": replacement_symbol,
                    ":": replacement_symbol,
                    ".": replacement_symbol,
                    ",": replacement_symbol}
                    
    for pattern, replacement in replace_dict.items():
        string = re.subn(re.escape(pattern), replacement, string)[0]
        
    # now remove multiple occurrences of the replacement symbol
    string = re.subn(f"{re.escape(replacement_symbol)}" + r"{1,}",
                    replacement_symbol, string)[0]        
        
    return string


def transcode(aax_file, activation_bytes,
                extension         = "mp3",
                codec             = "libmp3lame",
                id3_version_param = "-id3v2_version 3",
                split             = True,
                remove_full       = False):
    """ 
    Transcodes a specified aax file into one or more files of a
    specified audio format using ffmpeg.
    Optionally split files into chapters.
    """

    logging.info( f"Starting with file '{aax_file}'.")

    # get metadata from running ffprobe
    logging.info("Extracting metadata...")
    pipe = subprocess.Popen([shutil.which("ffprobe"), "-hide_banner", 
                                "-activation_bytes", activation_bytes,
                                "-i", aax_file],
                            stdin = subprocess.PIPE, stdout = subprocess.PIPE,
                            stderr = subprocess.PIPE)

    metadata_full = pipe.communicate()[1].decode()

    # extract book metadata (as opposed to chapter metadata)
    # first get rid of the carriage return
    # extract everything between "Metadata:\n" and "\n  Duration: "
    metadata_book = re.search(r"(?<= Metadata:\n).+(?=\n {2}Duration: )",
                              re.sub(r"\r", "", metadata_full),
                              re.DOTALL)

    # split into a list, each entry becomes an element
    metadata_book = metadata_book.group().split("\n")

    # convert the list to a dict
    meta_book = {}

    for entry in metadata_book:
        entry = entry.split(":", maxsplit = 1)
        meta_book[entry[0].strip()] = entry[1].strip()

    # extract further info from metadata
    bitrate = re.search(r"(?<=bitrate: )\d+", metadata_full).group()

    # generate file name and directories
    output_dir = (f"output/{sanitize(meta_book['genre'])}/"
                  f"{sanitize(meta_book['artist'])}/"
                  f"{sanitize(meta_book['title'])}")
    output_file = f"{output_dir}/{sanitize(meta_book['title'])}.{extension}"

    logging.info(f"Attempting to create path {output_dir}")
    pathlib.Path(output_dir).mkdir(parents = True, exist_ok = True)

    # now convert aax file to mp3
    os.system(f"ffmpeg -y -loglevel error"
              f" -activation_bytes  {activation_bytes}"
              f" -i \"{aax_file}\""
              f" -vn"
              f" -codec:a \"{codec}\""
              f" -ab {bitrate}k"
              f" -map_metadata"
              f" -1"
              f" -metadata title=\"{meta_book['title']}\""
              f" -metadata artist=\"{meta_book['artist']}\""
              f" -metadata album=\"{meta_book['album']}\""
              f" -metadata date=\"{meta_book['date']}\""
              f" -metadata track=\"1/1\""
              f" -metadata genre=\"{meta_book['genre']}\""
              f" -metadata copyright=\"{meta_book['copyright']}\""
              f" \"{output_file}\"")

    logging.info(f"Finished decoding, file at {output_file}")

    if split:
        # Now on to splitting the huge mp3 into chapters

        # read chapter metadata
        # match all the chapter lines
        # titles and other metadata get ignored at the moment
        metadata_chapters = re.findall(r"Chapter #0:\d+: start \d+.\d+, end "
                                        r"\d+.\d+\n    Metadata:\n      title"
                                        r"           : Chapter \d+\n",
                                        metadata_full)

        # Proceed through every chapter and cut main audio file according to
        #  chapter length
        for chapter in metadata_chapters:
            chapter_num_orig = re.search(r"(Chapter #0:)(\d+)",
                                         chapter).group(2)
            chapter_num      = int(chapter_num_orig) + 1
            chapter_start    = re.search(r"(?<= start )[\d.]+",
                                         chapter).group()
            chapter_end      = re.search(r"(?<= end )[\d.]+",
                                         chapter).group()
            chapter_duration = float(chapter_end) - float(chapter_start)
            chapter_title    = f"{meta_book['title']}_Chapter_{chapter_num:03}"
            chapter_file     = (f"{output_dir}/"
                                f"{sanitize(chapter_title)}.{extension}")

            logging.info( f"Obtained chapter metadata for chapter "
                          f"{chapter_num}.")
            logging.debug(f"Chapter metadata is:\n"
                            f"\tChapter number: {chapter_num}\n"
                            f"\tChapter start: {chapter_start}\n"
                            f"\tChapter end: {chapter_end}\n"
                            f"\tChapter duration: {chapter_duration}\n"
                            f"\tChapter title: {chapter_title}\n"
                            f"\tChapter file name: {chapter_file}")

            logging.info(f"Attempting to split chapter {chapter_num}...")

            # now do the splitting
            os.system(f"ffmpeg -hide_banner -loglevel error -y"
                    f" -i \"{output_file}\""
                    f" -ss \"{chapter_start}\""
                    f" -to \"{chapter_end}\""
                    f" -acodec \"{codec}\" {id3_version_param}"
                    f" -metadata track=\"{chapter_num}\""
                    f" -metadata title=\"{chapter_title}\""
                    f" -metadata:s:a title=\"{chapter_title}\""
                    f" -metadata:s:a track=\"{chapter_num}\""
                    f" \"{chapter_file}\"")

            logging.info(f"Done with chapter {chapter_num}.")

        # if the splitting was successful, we can remove the huge file
        if remove_full:
            logging.info(f"Done splitting, removing decoded "
                         f"{extension} file...")
            os.remove(output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = """
                                        AAX converter
                                        """)
    
    parser.add_argument("-i", "--infile",
                        nargs = "*",
                        type = str,
                        help = "Input files, if given, the .aax files among " 
                                "them will be converted. If not given, an "
                                "input dir has to be given with -d")

    parser.add_argument("-d", "--directory",
                        nargs = "*",
                        type = str,
                        help = "Directory/ies from which .aax files will be "
                                "converted.")

    parser.add_argument("-f", "--format",
                        type = str,
                        default = "mp3",
                        help = "Format abbreviation for the file format the "
                                "input files will be converted to. See ffmpeg "
                                "documentation on which ones are possible. "
                                "Default: mp3")

    parser.add_argument("-c", "--codec",
                        type = str,
                        help = "Encoder that ffmpeg should use, see their "
                                "documentation on possible options.")

    parser.add_argument("-b", "--debug",
                        action = "store_true",
                        help = "Set logging level to debug.")

    parser.add_argument("-a", "--authcode",
                        type = str,
                        help = "Personal audible activation code, see github "
                                "page on how to obtain it. If not given, a "
                                "'.authcode' file containing nothing but the "
                                "activation code needs to be in the current "
                                "directory.")

    parser.add_argument("-o", "--output",
                        type = str,
                        default = "./output",
                        help = "Output directory path.")
    
    args = vars(parser.parse_args())

    # configure logging module
    if args["debug"]:
        log_lvl = logging.DEBUG
    else:
        log_lvl = logging.INFO

    logging.basicConfig(level = log_lvl,
                        format = '%(asctime)s %(levelname)s: %(message)s')


    # define variables
    # (in the future these should get passed from command line)
    id3_version_param = "-id3v2_version 3"

    # set default extension encoder
    if args["format"] == "mp3" and args["codec"] is None:
        codec = "libmp3lame"

    # get input files
    aax_files = []

    # get all .aax files in the given directories
    if args["directory"] is not None:
        for dir in args["directory"]:
            p = pathlib.Path(dir)
            aax_it = p.glob("*.aax")
            dir_files = sorted(aax_it)

            # convert dir_files to string representations and add to overall
            #   file list
            aax_files = aax_files + [str(x) for x in dir_files]
                
    # get all individual .aax files
    if args["infile"] is not None:
        for file in args["infile"]:
            if re.search(".aax$", file):
                aax_files.append(str(pathlib.Path(file).expanduser()))

    if len(aax_files) == 0:
            print("No valid files provided.")
            sys.exit(0)

    # if no authcode arg is provided, assume there is a .authcode file in
    #   the current dir
    if args["authcode"] is None:
        authcode = ".authcode"
    
    # otherwise use whatever was given as the argument
    else:
        authcode = args["authcode"]

    # check if the authcode var is a path to somewhere
    if os.path.exists(authcode):
        # read authcode from file
        activation_bytes = open(authcode, "r").read().strip("\n")

    else:
        activation_bytes = authcode

    # check if the authcode is a hex number
    if not re.match(r"[0-9a-fA-F]+", activation_bytes):
        print("No valid authcode provided and no valid '.authcode' file " 
                "found.")
        sys.exit(0)


    # start main transcoding loop
    for aax_file in aax_files:
        transcode(aax_file, activation_bytes,
                    args["format"], codec, id3_version_param,
                     remove_full = True)

    logging.info("All done.")
