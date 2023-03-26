# i2cbright

Set brightness via i2c using DDC protocol

## Background

Modern external monitors support modifying their brightness levels via the DDC
protocol over i2c.  From userspace, under Linux, there are many tools to
accomplish this via the userspace i2c driver mechanism (i2c-dev).

In particular, the well-known [ddcutil](https://www.ddcutil.com/) project was
used as a reference during the development of this project.

## Constraints

I run [Fedora Silverblue](https://silverblue.fedoraproject.org/) without
overlays, and was interested in a solution that I could use without installing
any additional packages.  That means the solution had to be able to exist
entirely within my home directory and/or `/etc`.  A simple Python script fit
the bill here.

I also wanted to improve on the detection logic of `ddcutil`, which in its
default mode, tries to open every `/dev/i2c-*` device node it finds,
complaining about permission problems where it can't.  I also wanted a
dramatically simplified interface that does exactly one thing: sets brightness.

It's not possible to query brightness (or set the brightness relative to the
current level) because reading the current brightness involves multiple i2c
packets and the necessary delays between them, which would substantially
complicate the code.  Maybe some day — but see "Future directions" below.

## Installation notes

In order for this all to work, the following must happen:

 - the `i2c-dev` module needs to be loaded to get the `/dev/i2c-*` devices exposed
 - your user need to be given access to the device for your monitor

`00-i2cbright.rules` in `data` will do both of those.  If you install this
package into `/usr` or `/usr/local` then this file will land in the correct
place. Otherwise, drop it in `/etc/udev/rules.d`.

The udev rules will load the module.  This might have been done cleaner with a
file in `modules-load.d`, but this file isn't searched for in `/usr/local`,
which is otherwise a fairly reasonable place to install this package.

## Future directions

Poking at i2c devices from userspace via i2c-dev with a strange Python script
is not my idea of a good time. Ideally this would be handled in the kernel via
some kind of a backlight interface.  There have been multiple attempts to merge
patches to this effect:

 - https://lore.kernel.org/lkml/20170121183151.8313-1-me@milek7.pl/
 - https://lore.kernel.org/lkml/20220403230850.2986-1-yusisamerican@gmail.com/

The current direction seems to be waiting on the creation of a new interface
that more directly couples the backlight drivers (which are their own class)
with the DRM display devices to which they correspond:

 - https://lore.kernel.org/lkml/7f2d88de-60c5-e2ff-9b22-acba35cfdfb6@redhat.com/
 - https://kernel-recipes.org/en/2022/talks/new-userspace-api-for-display-panel-brightness-control/

Until this lands in the kernel, though, this script represents a reasonable
hack.
