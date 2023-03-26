#!/usr/bin/python3

# i2cbright - Set brightness via i2c using DDC protocol
#
# Copyright (C) 2022 Allison Karlitskaya <allison.karlitskaya@redhat.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import fcntl
import functools
import glob
import logging
import operator
import os
import re
import sys

from typing import BinaryIO

DDC_ADDR = 0x37


def find_output(edid_str: bytes) -> str:
    edid_filenames = glob.glob('/sys/class/drm/*/edid')
    for filename in edid_filenames:
        logging.debug('Considering edid file %s', filename)
        with open(filename, 'rb') as edid:
            if edid_str in edid.read():
                logging.debug('  got a match')
                return os.path.dirname(filename)
    sys.exit('Unable to find a monitor with the given EDID substring')


def find_devices(output: str) -> str:
    uevent_filenames = glob.glob(f'{output}/i2c-*/i2c-dev/i2c-*/uevent')
    for filename in uevent_filenames:
        logging.debug('Considering uevent file %s', filename)
        with open(filename) as uevent:
            match = re.search(r'^DEVNAME=(.*)$', uevent.read(), flags=re.M)
            if match:
                logging.debug('  got match: %s', match)
                return '/dev/' + match.group(1)
    sys.exit('Unable to find i2c device for the specified monitor.  modprobe i2c-dev?')


def open_i2c(filename: str) -> BinaryIO:
    logging.debug('Opening i2c device %s', filename)
    file = open(filename, 'ab+', buffering=False)
    logging.debug('Setting i2c device address %x', DDC_ADDR)
    fcntl.ioctl(file.fileno(), 0x0703, DDC_ADDR)
    return file


def mkpacket(packet):
    packet = [len(packet) | 0x80] + packet
    # we calculate the checksum as if 0x80|DDC_ADDR were the first byte
    packet.append(0x80 ^ DDC_ADDR ^ functools.reduce(operator.xor, packet))
    logging.debug('Calculated packet contents: %r', packet)
    return bytes(packet)


def set_brightness(value):
    return mkpacket([
        0x51,  # source address
        0x03,  # write
        0x10,  # brightness
        0x00,
        value
    ])


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dev', help="Directly specify the i2c-dev device, eg. /dev/i2c-11")
    group.add_argument('--drm', help="Directly specify the monitor sysfs path, eg. /sys/class/drm/card1-DP-1")
    group.add_argument('--edid', help="Search via EDID substring, eg. DELL")
    parser.add_argument('--debug', action='store_true', help="Display debug info")
    parser.add_argument('brightness', type=int, help="Brightness to set (eg. 75)")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    dev = args.dev or find_devices(args.drm or find_output(args.edid.encode()))
    with open_i2c(dev) as bus:
        bus.write(set_brightness(args.brightness))


if __name__ == '__main__':
    main()
