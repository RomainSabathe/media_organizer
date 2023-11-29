# Media Organizer

> A simple python utility with two goals in mind:
> 1. Organize and rename media files into folders based on their capture datetime
> 2. Sync the capture datetime of files coming from different cameras

## :warning: Warning

I've used this project successfully for some of my own media files, but it's still a work in progress. The biggest flaw is that it is slow. It's using batched calls to exiftool, but even then
processing ~50 GB of data can take up to several hours.

## Alternative solutions

If you're looking for a similar solution, I've had good experience with the following:

* [exifrename](https://github.com/cdown/exifrename) - A rust tool, Linux only. It's extremely fast and configurable but doesn't work with videos at the moment.

Other mentions:

* [Elodie](https://github.com/jmathai/elodie)
* [Phockup](https://github.com/ivandokov/phockup)


Other options I want to try:

* [PhotoMove](https://www.mjbpix.com/automatically-move-photos-to-directories-or-folders-based-on-exif-date/) - Promising piece of software. Supports video files. But doesn't rename the files themselves and the folder structure doesn't seem to be customizable.
* [PhotoSort](https://github.com/fialot/PhotoSort) - C# tool. Offers the possibility to sync the datetime coming from different cameras. But it is quite old.
