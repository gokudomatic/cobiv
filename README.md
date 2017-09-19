# cobiv
COmmand Based Image Viewer

This application is yet another DAM (Digital Asset Managemenet) build out of frustration from the lack of specific features in the other viewers. But it's quite different from the existing solutions in many aspects, as it is answering to specific needs that go out of the usual scope of such applications.

The highlight features of this application are:
* Powerful search engine for images, based on custom tags and image properties.
* Internal duplicate images finder.
* Imagesets organizer.
* Mass file operations, like tagging, moving and deleting files.
* Fully extensible through plugins. Whether it's adding support for a file format, extending features, making a custom user interface or adding a whole new module, it's possible to develop anything using Python and Kivy.
* Scalability, supporting very large catalogs of images without performance degradation. Only the internal search engine can become slow with large amounts of files (above 500'000 images), which can be replaced with a more powerful external database.
* Adapted for any kind of screen size, even the smallest ones and the largest ones.
* Touch screen friendly.
* Totally controlable with a keyboard, with an integrated VI-like command prompt.
* Capability to connect to various filesystems (NAS, zip files, ftp, WebDAV...).
* Multiplatform, as long as Python can run on it.

## Original purpose
While lot of free image viewer applications exist already with more or less specific features, I didn't find any that let me both :
* browse multiple images with keys to navigate
* have an uncluttered fullscreen UI
* search images with tags, with categories, inclusion and exclusion
* easily tag images on the fly when browsing
* import images in some kind of big repository and automatically remove duplicates
* prevent deleted unwanted images to be imported again
* handle comics as a set sorted by filename but search the set as a single entry, allowing to manage a catalog of comics

Digikam was the closest alternative I found, but I found it quite cluttered and not very easy for watching images fullscreen.

And while I didn't really wanted to go on a full development of an application, the fact is, I need those features. And since I got already some neat and interesting experience with Kivy, the idea of making a very basic but pragmatic viewer, implementing only what I need even if it looks incredibly rough on the edges, seemed then to be realistical and not much time consuming. But then, as a developer, I like to keep things reusable, customizable and powerful. Cue the idea of using VI's concept, which is famous for being all of that. Downside of VI is its huge learning curve. But with Kivy and Python, there's a whole playground for interesting new UI to invent.


## VI
Cobiv was build with extensibility in mind. Also, the initial needs were a minimal UI totally controlable with either keyboard or touch screen only (no need for a mouse). And since this viewer isn't targeting a beginner audience rather power users, the architecture of VI was the inspiration of the core of Cobiv. Every action is initially a command that can be entered by pressing ":" and then the command name. On top of that are implemented hotkeys, gestures, and visual components that call the same commands. Commands can be contextual or global, as well as the hotkeys.
Thanks to this system, it is possible to integrate macros and bind a key to any kind of action or macro. Also, it allows plugins to easily add features through new commands.

It is not required to use the command line at all. Visual layouts and gestures are also available, especially for touch screens. 

## Views
Cobiv is composed of views, which are the visual screens. One view is for help, another is for visualizing images and another is for managing the current imageset. Adding a new view, like for instance an ftp file browser, an image editor or even a music player, is very straightforward thanks to the plugin system.

## User interface
The user interface is anything but looking native, mostly because of Kivy. Kivy is meant to be a common UI framework for both desktop and mobile. Therefore every component is rendered by Python, using the GPU acceleration. Since it wasn't possible from the beginning to make a native looking app, the idea was then to make a whole new user interface and break the standards in order to use the full capabilities of Kivy.
Like for Blender, which also use its own unique kind of UI, cobiv can be hard to learned at the beginning. Also, the UI is very oriented toward keyboard only users and touch screen users. Traditional mouse users would be pretty disappointed for the lack of visual options and the overall ergonomy made for fingers rather than a cursor. Digikam is a much better alternative for them, and cobiv never intended to be a copy of this kind of application.

## Performance and database
Cobiv uses by default SQLite for file indexing and tag searching. The default search engine generates SQL from cobiv's search syntax, which supports functions and access to variables (like for instance the date of the currently selected image). The functions can also be extended via plugins, which should provide more than enough flexibility to do almost any kind of search and sort. The performance of the search is however very dependant to the kind of query and it can be rather slow with large databases. It is however possible to switch for another database through plugins, as long as the plugin exists. The cursor is an abstract interface and it can be implemented for any kind of database engine, from a classical Postgres to a nosql Mongodb or a file based database. It can be also a mix of various databases and memory caches (key storage and others), as long as Python can handle it.

A test with one million entries and a total of 4 millions tags showed up that a query from cobiv in SQLite takes from 1.5 seconds to 30 seconds on a low spec computer, depending on the complexity of the query.

Once the search is done, the generated resultset is displayed in an infinite list viewer, which guarantees to browse the files at a consistant performance, no matter how large the resultset is.

## Search syntax
To search images, it is possible through a syntax to set criterias of various kinds.
To search just tags, you write:
:search tag1 tag2 tag3 ... tagN
Example:
:search trip island john

### Categories
To search a tag in a category, you write:
:search category:tag
Example:
:search animal:dog background:house

### Exclusion and number casting
You can exclude tags with the minus character "-". Example:
:search show:ducktales -character:donald -mexico
Which would return all pics about the show "Ducktales" without both the character Donald and being tagged mexico. 

Tags are by default considered as alphabetic text. When sorting by a category of tag or when comparing tags with greater or lesser than a value, numbers will be considered as text rather than numbers. That leads to incoherent results, for instance where "2" is greater than "19". To avoid that problem, you can cast the criteria as number with the sharp character "#". Example:
:search #zip:10118

### Comparators
A tag can be searched with various comparators. The most common is the equality comparator, checking that the value is exactly the same in the criteria as in the tag value. But it is possible to compare partial text and numbers (including dates).


### Functions

### File information
Properties of the file can be searched like any other category. Example:
:search format:PNG width:800 height:600
It returns every PNG image with dimension 800x600.

The available categories are:
* file_date : modification date of the file, stored as unix timestamp (number of seconds since epoch)
* size : size of the file, in byte
* ext : extension of the file (3 last characters extracted from the filename)
* path : path of the folder containing the file

