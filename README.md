# lzw-python

A minimalistic [LZW](https://en.wikipedia.org/wiki/Lempel%E2%80%93Ziv%E2%80%93Welch) implementation in Python 3, compatible with Unix [compress](https://en.wikipedia.org/wiki/Compress) program (typically **.Z** extension).

## Usage

```
$ python3 lzw.py --help
usage: lzw.py [-h] [-d] [-o OUTPUT] INPUT

LZW Compress/Decompress

positional arguments:
  INPUT                 Input file

optional arguments:
  -h, --help            show this help message and exit
  -d, --decompress      Decompress mode
  -o OUTPUT, --output OUTPUT
                        Output file
```

## Test

```
$ python3 lzw.py -o test/output.txt.Z test/Lorem_Ipsum.txt
$ sudo apt install ncompress
$ compress -d test/output.txt.Z
```

## License

GPL-3.0
