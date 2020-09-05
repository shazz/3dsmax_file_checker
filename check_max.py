import re, os, glob, uuid, shutil, subprocess
import colorama
from colorama import Fore, Style
from os.path import basename

def convert_version_to_date(ver):
    if ver > 9:
        ver += 1998 #setting 3ds Max version
    elif ver <= 9:
        ver += 1997

    return ver

def getVersion(st, line):
    i = line.index(st)+len(st) #getting string position
    ver = line[i:i+5]
    ver = re.sub('[^0123456789.]', '', ver) #getting version number
    ver = ver.rstrip('0')
    ver = ver.rstrip('.')
    ver = convert_version_to_date(int(ver))

    return ver

def reverse_readline(filename): # big thanks to srohde and Andomar at http://stackoverflow.com for this piece of code!
    """a generator that returns the lines of a file in reverse order"""
    buf_size=8192

    with open(filename, 'rt', encoding='latin-1') as fh:
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        file_size = remaining_size = fh.tell()
        while remaining_size > 0:
            offset = min(file_size, offset + buf_size)
            fh.seek(file_size - offset)
            buffer = fh.read(min(remaining_size, buf_size))
            remaining_size -= buf_size
            lines = buffer.split('\n')
            # the first line of the buffer is probably not a complete line so
            # we'll save it and append it to the last line of the next buffer
            # we read
            if segment is not None:
                # if the previous chunk starts right from the beginning of line
                # do not concact the segment to the last line of new chunk
                # instead, yield the segment first
                if buffer[-1] != '\n':
                    lines[-1] += segment
                else:
                    yield segment
            segment = lines[0]
            for index in range(len(lines) - 1, 0, -1):
                if len(lines[index]):
                    yield lines[index]
        # Don't yield None if the file was empty
        if segment is not None:
            yield segment

def getFileVersion(maxFile): # check .max file version
    savedVer = 'SavedAsVersion:'
    maxVer = '3dsmaxVersion:'

    renderer = None
    version = None

    for line in reverse_readline(maxFile):

        cleanLine = re.sub('[^AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789.:]', '', line) #filtering out unneeded characters
        if cleanLine:
            if savedVer in cleanLine:
                version =  getVersion(savedVer, cleanLine)
            elif maxVer in cleanLine:
                version =  getVersion(maxVer, cleanLine)

        if renderer and version:
            break

    return version

def find_full_string_from_extension(data, idx):

    end_of_str = idx + 4

    v = ord(data[idx])
    while v != 0:
        idx = idx - 1
        v = ord(data[idx])

    return data[idx+1: end_of_str]

def detect_interleaved_data(data):
    idx = data.find(b'\x47\x00\x65\x00\x6e\x00\x65\x00\x72\x00\x61\x00\x6c')
    return idx != -1

def find_full_string_from_start(data, idx):

    start = idx
    v = ord(data[idx])
    while v != 0:
        idx = idx + 1
        v = ord(data[idx])

    return data[start: idx]


def find_textures(data, extension, textures_files):
    idx = data.find(extension)
    while idx != -1:
        tex = find_full_string_from_extension(data, idx)
        textures_files.append(tex)
        idx = data.find(extension, idx+1)

def find_param(data, param):
    value = None

    idx = data.find(param)
    if idx != -1:
        value = find_full_string_from_start(data, idx+len(param))

    return value


def decompound_file(filename):

    data = None
    textures_files = []
    textures_ext = ['.jpg', '.JPG', '.png', '.PNG', '.tif', '.TIF', '.bmp', '.bBMP']

    file_id = uuid.uuid4()
    tmp = "tmp/{}/".format(file_id)

    subprocess.run(["7z", "x", filename, "-o{}".format(tmp), "-bb0"], capture_output=False, stdout=subprocess.DEVNULL)

    with open("tmp/{}/[5]DocumentSummaryInformation".format(file_id), "rb") as bin_desc:
        data_bin = bin_desc.read()

    if detect_interleaved_data(data_bin):
        print("File is interleaved, need some cleaning")
        data_bin = data_bin.replace(b'\x00\x00', b'\x20\x20')
        data_bin = data_bin.replace(b'\x00', b'')
        data_bin = data_bin.replace(b'\x20\x20', b'\x00')
        data = data_bin.decode('latin-1')
    else:
        print("File is not interlaced")
        with open("tmp/{}/[5]DocumentSummaryInformation".format(file_id), "r",  encoding='latin-1') as desc: #errors='ignore'
            data = desc.read()

    # parsing params
    objects = find_param(data, 'Objects: ')
    vertices = find_param(data, 'Vertices: ')
    faces = find_param(data, 'Faces: ')

    print(f"Objects: {objects}")
    print(f"Vertices: {vertices}")
    print(f"Faces: {faces}")

    # find textures
    for texture_ext in textures_ext:
        find_textures(data, texture_ext, textures_files)

    # remove dups
    textures_files = list(set(textures_files))

    print(f"Textures expected: {Fore.BLUE}{None if len(textures_files) == 0 else len(textures_files)}{Fore.WHITE}")
    for tex in textures_files:
        print(" - {}".format(tex))

    renderer = find_param(data, 'Renderer Name=')
    version = find_param(data, '3ds Max Version: ')
    if version is None:
        version = find_param(data, '3ds max Version: ')

    saved_version = find_param(data, 'Saved As Version: ')

    # clean version
    if version is not None:
        max_version = float(version.replace(',', '.'))
        max_converted = convert_version_to_date(int(max_version))

    if saved_version is not None:
        saved_version = float(saved_version.replace(',', '.'))
        converted = convert_version_to_date(int(saved_version))
    else:
        converted = getFileVersion(filename)

    print(f"Renderer: {renderer}")
    print(f"3ds max Version: {max_converted}")
    color = Fore.GREEN if converted < 2018 else Fore.RED
    print(f"Save version: {color}{converted}{Fore.WHITE}")

    print("deleting temp files in {}".format(tmp))
    shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":

    colorama.init()

    max_files =  glob.iglob('**/tobeanalyzed/*.max', recursive=True)

    for max_file in max_files:

        print("----------------------------------------------------------------")
        print(f"Analyzing: {Fore.BLUE}{basename(max_file)}{Fore.WHITE}")

        decompound_file(max_file)


