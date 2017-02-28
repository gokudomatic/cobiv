# cobiv
COmmand Based Image Viewer

This application is yet another image viewer build out of frustration from the lack of specific features in the other viewers. But it's quite different from the existing solutions in many aspects, as it is answering to specific needs that go out of the usual scope of such applications.

The highlight features of this application are:
* Powerful search engine for images, based on custom tags and image properties.
* Duplicate images finder, using ImageMagick.
* Imagesets organizer.
* Mass file operations, like tagging, moving and deleting files.
* Full extensibility through plugins. Whether it's adding support for a file format, extending features, making a custom user interface or adding a whole new module, it's possible to develop anything using Python and Kivy.
* Scalability, supporting very large catalogs of images without performance degradation.
* Adapted for any kind of screen size, even the smallest ones and the largest ones.
* Touch screen friendly.
* Totally controlable with a keyboard, with an integrated VI-like command prompt.
* Capability to connect to various filesystems (NAS, zip files, ftp, WebDAV...).
* Multiplatform.

## VI
Cobiv was build with extensibility in mind. Also, the initial needs were a minimal UI totally controlable with either keyboard or touch screen only (no need for a mouse). And since this viewer isn't targeting a beginner audience rather power users, the architecture of VI was the inspiration of the core of Cobiv. Every action is initially a command that can be entered by pressing ":" and then the command name. On top of that are implemented hotkeys, gestures, and visual components that call the same commands. Commands can be contextual or global, as well as the hotkeys.
Thanks to this system, it is possible to integrate macros and bind a key to any kind of action or macro. Also, it allows plugins to easily add features through new commands.

It is not required to use the command line at all. Visual layouts and gestures are also available, especially for touch screens.

## Views
Cobiv is composed of views, which are the visual screens. One view is for help, another is for visualizing images and another is for managing the current imageset. Adding a new view, like for instance an ftp file browser, an image editor or even a music player, is very straightforward thanks to the plugin system.

## User interface
The user interface is anything but looking native, mostly because of Kivy. Kivy is meant to be a common UI framework for both desktop and mobile. Therefore every component is rendered by Python, using the GPU acceleration. Since it wasn't possible from the beginning to make a native looking app, the idea was then to make a whole new user interface and break the standards in order to use the full capabilities of Kivy.
Like for Blender, which also use its own unique kind of UI, cobiv can be hard to learned at the beginning.
