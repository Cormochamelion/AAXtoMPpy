import os
import pathlib
import re
import logging
import subprocess

# configure logging module
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# define variables (in the future these should get passed from command line)
extension = "mp3"
codec = "libmp3lame"
id3_version_param = "-id3v2_version 3"


def sanitize(string, replacement_symbol="_"):
    """ Turns filesystem-unfriendly characters into whatever is specifies by replacement_symbol (Default: "_") """
    replace_dict = {" ": replacement_symbol,
                    ":": replacement_symbol,
                    ".": replacement_symbol,
                    ",": replacement_symbol}
    for pattern, replacement in replace_dict.items():
        string = re.subn(re.escape(pattern), replacement, string)[0]
        # now remove multiple occurrences of the replacement symbol
        string = re.subn(f'{re.escape(replacement_symbol)}+', '', string)[0]
    return string


# get directory with aax files
aax_dir = os.getcwd() + '\\aax_input'

# read authcode from file
activation_bytes = open(".authcode", "r").read()

# get all .aax files in input dir
aax_files = list(filter(re.compile(r"\.aax$").search, os.listdir("aax_input")))

# start main transcoding loop
for aax_file in aax_files:

    aax_file_path = f"{aax_dir}\\{aax_file}"

    logging.info(f"Starting with file '{aax_file}'.")
    logging.debug(f"Full file path is {aax_file_path}")

    # get metadata from running ffprobe
    logging.info("Extracting metadata...")
    pipe = subprocess.Popen(f"ffprobe -hide_banner -activation_bytes {activation_bytes} -i \"{aax_file_path}\"",
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    metadata_full = pipe.communicate()[1].decode()

    # extract book metadata (as opposed to chapter metadata)
    # first get rid of the carriage return
    # extract everything between "Metadata:\n" and "\n  Duration: "
    metadata_book = re.search(r"(?<= Metadata:\n).+(?=\n {2}Duration: )", re.sub(r"\r", "", metadata_full), re.DOTALL)

    # split into a list, each entry becomes an element
    metadata_book = metadata_book.group().split("\n")

    # convert the list to a dict
    meta_book = {}

    for entry in metadata_book:
        entry = entry.split(":", maxsplit=1)
        meta_book[entry[0].strip()] = entry[1].strip()

    # extract further info from metadata
    bitrate = re.search(r"(?<=bitrate: )\d+", metadata_full).group()

    # generate file name and directories
    output_dir = f"output\\{sanitize(meta_book['genre'])}\\{sanitize(meta_book['artist'])}" \
                 f"\\{sanitize(meta_book['title'])}"
    output_file = f"{output_dir}\\{sanitize(meta_book['title'])}.{extension}"

    logging.info(f"Attempting to create path {output_dir}")
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    # now convert aax file to mp3
    os.system(f"ffmpeg -y -activation_bytes  {activation_bytes} -i \"{aax_file_path}\" -vn"
              f" -codec:a \"{codec}\" -ab {bitrate}k"
              f" -map_metadata -1 -metadata title=\"{meta_book['title']}\" -metadata artist=\"{meta_book['artist']}\""
              f" -metadata album=\"{meta_book['album']}\" -metadata date=\"{meta_book['date']}\""
              f" -metadata track=\"1/1\" -metadata genre=\"{meta_book['genre']}\""
              f" -metadata copyright=\"{meta_book['copyright']}\""
              f" \"{output_file}\"")

    logging.info(f"Finished decoding, file at {output_file}")

    # Now on to splitting the huge mp3 into chapters

    # read chapter metadata
    # match all the chapter lines, titles and other metadata get ignored at the moment
    metadata_chapters = re.findall(r"(?<=Chapter #0:).+(?=\r)", metadata_full)

    # Proceed through every chapter and cut main audio file according to chapter length
    for chapter in metadata_chapters:
        chapter_num_orig = re.search(r"\d+", chapter).group()
        chapter_num = int(chapter_num_orig) + 1
        chapter_start = re.search(r"(?<= start )[\d.]+", chapter).group()
        chapter_end = re.search(r"(?<= end )[\d.]+", chapter).group()
        chapter_duration = float(chapter_end) - float(chapter_start)
        chapter_title = f"{meta_book['title']}_Chapter_{chapter_num:03}"
        chapter_file = f"{output_dir}\\{sanitize(chapter_title)}.{extension}"

        logging.info(f"Obtained chapter metadata for chapter {chapter_title}.")
        logging.debug(f"Chapter metadata is:\n\tChapter number: {chapter_num}\n\tChapter start: {chapter_start}\n\t"
                      f"Chapter end: {chapter_end}\n\tChapter duration: {chapter_duration}\n\t"
                      f"Chapter title: {chapter_title}\n\tChapter file name: {chapter_file}")
        logging.info(f"Attempting to split chapter {chapter_title}...")

        # now do the splitting
        os.system(f"ffmpeg -hide_banner -y -i \"{output_file}\""
                  f" -ss \"{chapter_start}\" -to \"{chapter_end}\""
                  f" -acodec \"{codec}\" {id3_version_param}"
                  f" -metadata track=\"{chapter_num}\" -metadata title=\"{chapter_title}\""
                  f" -metadata:s:a title=\"{chapter_title}\" -metadata:s:a track=\"{chapter_num}\""
                  f" \"{chapter_file}\"")

        logging.info(f"Done with chapter {chapter_num}.")

    # if the splitting was successful, we can remove the huge file
    logging.info(f"Done splitting, removing decoded {extension} file...")
    os.remove(output_file)

logging.info("All done.")
