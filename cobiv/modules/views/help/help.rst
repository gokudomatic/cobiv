====================================
COBIV - COnsole Based Image Viewer
====================================

::

  Version 0.0.1 alpha
  by Edwin Cox
  Cobiv is open source under MIT license and freely distributable


========================== ====================================
**Type**                   **Action**
-------------------------- ------------------------------------
*<up arrow>*               to scroll up
*<down arrow>*             to scroll down
:q *<Enter>*               to exit
:help *<Enter>*            for on-line info
:switch-view {view-name}   to switch to a specific view
/{search query} *<Enter>*  start a search with the given query
========================== ====================================

:Notes: Any text in <...> are keyboard keys. *<Enter>* is the enter key.

    Texts in {...} are custom parameters to be entered by the user. The characters { and } must not be entered.

Quickstart
----------


Introduction
------------
Cobiv is a digital asset manager (DAM) mostly focused on organizing and retrieving images.
It is written in Python with Kivy, and therefore it can run on any platform that supports Python and OpenGL.

Cobiv is heavily inspired by the in-terminal text editor VI. Even though VI is a command line based editor, Cobiv runs
on its own window. But it shares the concept of executing commands by typing them, which provides scripting features and
the ability to command Cobiv with a mere keyboard (a mouse is not required). Thanks to the framework Kivy, Cobiv also
features touch screen support, and by extension also mouse support. The main target platforms of Cobiv are desktop computers
and laptops with touch screen.

Like in VI, the main idea of this application is speed and modularity. The user interface is not meant to be easy to learn
but it focuses more on simplicity and efficiency. Its integrated plugin system allows to add or replace features on every
level of the application. The idea behind that is to give the ability to customize at will Cobiv for the user's particular needs.
Therefore the core of the application is meant to be lightweight and very extensible with plugins written in Python.

The default plugins for image management are also meant to be basic but very performing in their task, which are:

* Handle very large sets of images, up to million files.
* Advanced fast search images by tags, including functions and comparators.
* Sort by multiple tags.
* Customizable user interface.
* Mass tagging.

For performance, SQLite is used as the main engine for both tagging and search. It is possible to change it with another
database for better performances via plugins. This allows fast search on even low end laptops and netbooks.

Overview
--------
Cobiv being a modular program, it is composed of a core and plugins. The core is the overall layout, with a command bar
and overlays, but except for that it only take care of background tasks, configuration and the plugin loader.

:Views:
        The most important type of plugin is the view. It is like a mini application and it defines what's on screen. This help
        screen is a view that display a formated text. The image viewer, which display one image at a time, is another view.
        The thumbnail browser is yet another kind of view. Each view has its own implementation and it can be pretty much anything
        visual. From an image editor to a video player, or even a torrent downloader or a spreadsheet application, as long as
        it's possible to do it in Kivy, it can be implemented as plugin in Cobiv.

:HUD:
        Hud plugins are visual widgets that can be added on top of the current view or in the overlays.

:I/O:
        This plugin are file readers or writers. It can be image file formats, like TIFF or PCX, or streams on an internet url.
        In the default image viewer plugins, they are mostly used to define which tags to read or write.

:Database:
        Since Cobiv uses a database to speed up the search and index, it is possible to configure connectors for new kinds
        of databases. Whether it is another SQL compatible database, a NoSQL database or a mere file based database,
        as long as the interfaces for it are implemented, Cobiv can use it. Performance is very depend of the quality of
        implementation and the inherent speed of the database engine behind.

:Entities:
        Every other kinds of plugin that are Python data structures or tools.

Thumbnail Browser plugin
---------------


Image Viewer plugin
--------------

Searching images
----------------
To search images, the command is:

::

    :search criteria1 [criteria2 criteria3 ... criteriaN]

where a criteria syntax is:

::

    [-][kind:[fn:]]arg1[:arg2:arg3:...:argN]

:arg1..N: keywords in tags to search. Only the first one is required.
:kind:    kind of tag to delimite the search. By default it's *, which means all kinds.
:fn:      Comparator function to use. The possible functions are :

    - in  : search in tags that are one of the keywords of the list. Only tags with exact match are returned.
    - %   : partial text search. Text must also contain the character % to tell where it should try all possibilities.
    - <   : numeric comparator of lesser than arg1. The field is considered as a float.
    - <=  : numeric comparator of lesser or equals than arg1. The field is considered as a float.
    - >   : numeric comparator of greater than arg1. The field is considered as a float.
    - >=  : numeric comparator of greater or equals than arg1. The field is considered as a float.
    - ><  : numeric comparator of between arg1 and arg2. The field is considered as a float.
    - YY  : date comparator of within year. Args must be years in 4 digits (YYYY).
    - YM  : date comparator of within year and month. Args must be years in 4 digits and month in 2 digits (YYYYMM).
    - YMD : date comparator of within year, month and day. Args must be years in 4 digits, months in 2 digits and days in 2 digits (YYYYMMDD).

The general rule for multiple arguments is as follow. The query is divided in groups by space. Each group is required.
The boolean operator for groups is AND.

Within a group, each argument is separated by the character : and the boolean operator for arguments is OR.

Therefore a query that looks like :
::

    arg1:arg2:arg3 argA argB:argC

will be translated as :
::

    (arg1 or arg2 or arg3) and argA and (argB or argC)

:Note: kinds of tag, also known as categories, can be anything, even information of the file or the image, like its size or dimension.
    Some pre-etablished kinds that are sure to be always present, like the file modification date or the file size, are stored in
    a separate table than the custom tags. They can be searched the same way as any other kind of tag. But for performance's
    sake the search on any kind of tag (*) won't search in those special tags. The kind must be specified in order to search
    in those special kinds of tags.

**Examples :**
::

    Searching any image tagged mountain
    :search mountain

    Searching any image tagged cat in kind pet and which was dated from 2015 :
    :search pet:cat file_date:YY:2015

    Searching any image tagged either john or peter but also with any tag starting with Samant
    :search john:peter *:%:Samant%

    Searching any image whose dimensions are 800x600 or less
    :search width:<=:800 height:<=:600

    Searching a combination of multiple kinds of tags, as an icon of 32x32 with 16 bits color, dated in januar 2017, extension is either ico or bmp, and tagged outlook.
    :search width:32 height:32 color_dept:16 file_date:YM:201701 outlook ext:ico:bmp

Sorting images
--------------


Functions
---------

Tagging
-------
