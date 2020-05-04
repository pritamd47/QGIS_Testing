# Developer Guide

## Branching
There are three branches.
1. `master` &rightarrow; Main Branch. Stable code goes here.
2. `dev` &rightarrow; Main development branch.
3. `sarthak_dev` &rightarrow; Development branch for [@sar1hak](https://github.com/Sar1hak). Make changes in this branch and push. To merge the changes, [create a pull request](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request), from `sarthak_dev` to `dev`. [@pritamd47](www.github.com/pritamd47) will review and merge if no conflicts found.

## Committing rubrics (from [deepsource](https://deepsource.io/blog/git-best-practices/))
1. Make clean, single-purpose commits
    - Try to work only on one problem, and commit the fix/improvement/feature as a single commit.
2. Write meaningful commit message
    - The message should describe what changes have been made.
3. Commit in small chunks, but not half-done work
    - Commit in small chunks, and often. Need not push, but committing small changes is a good idea, without worrying about the perfect commit - but do not forget to explicitly declare what changes were made in the commit. Half-done work should not be committed though, best is to break any problem in small chunks, and commit each chunk separately.
4. Try to use GitKraken for git control. Very intuitive and is a nice learning platform - they also have youtube videos describing various git version control commands.
5. When in doubt, contact [@pritamd47](www.github.com/pritamd47)

## Code Style
1. [`pep8`](https://www.python.org/dev/peps/pep-0008/) not strict, but things like limiting line length to 79 characters, and proper naming convention is a good idea. What to follow from `pep8`:
    - [Indentation](https://www.python.org/dev/peps/pep-0008/#id17)
    - [Line Length](https://www.python.org/dev/peps/pep-0008/#id19)
    - [Blank Lines](https://www.python.org/dev/peps/pep-0008/#id21)
    - [Pet Peeves](https://www.python.org/dev/peps/pep-0008/#id27)
    - [Comments](https://www.python.org/dev/peps/pep-0008/#id30). Comment extensively - Docstrings are must.
    - [Naming Conventions](https://www.python.org/dev/peps/pep-0008/#id30). Not set on stone, but try to follow this. Note that, some of the code doesn't follow this, because of conventions of Qt and QGIS.
     

## Setting up Development Environment
1. Start by installing QGIS from [here](https://qgis.org/en/site/forusers/download.html#). Use the OSGeo4W installer.
2. Go to `Plugins` > `Manage and Install Plugins`. Search for `Plugin Reloader` and install the plugin.
3. Go to and click `Settings` > `User profiles` > `Open active profile folder`. From there, navigate to `python` > `plugins` and note down the path. This path will be used later to configure the compiler.
4. Go to a directory of choice and `git clone https://github.com/pritamd47/CMProcessing.git`.
5. Open up terminal and run `pip install pb_tool`. I don't think conda has this tool (`pb_tool`).
6. Get inside the directory `CMProcessing` (or the directory where repo was cloned). There you'll find a file named `pb_tool_win.cfg`. Change the line `plugin_path: C:\Users\prita\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins` to `plugin path: [path of plugin directory as noted in step 3]`.
7. Download [QTCreator for Windows](https://download.qt.io/official_releases/qtcreator/4.11/4.11.0/qt-creator-opensource-windows-x86_64-4.11.0.exe) if your system is windows-64 bit. If not, go to this [link](https://www.qt.io/offline-installers) and navigate to `QT Creator` to find the installer suitable for your machine. This will be used to open the `.ui` files in `CMProcessing`.
8. Once all this is done, navigate to CMProcessing in a terminal and `pb_tool deploy --config_file pb_tool_win.cfg`. Congratulations! If everything has been nice and dandy till now.
9. Restart QGIS and click on `Plugins` > `Manage and Install Plugins` > `Installed`. Find the plugin named `Snow Melt runoff modelling Data Pre-Processing` and check the checkbox. The plugin should now work, and clicking on it (located at `Plugins` > `Snow Melt runoff modelling Data Pre-Processing`) should open up a Dialog Box – albeit without any functionality. From this point, any changes made to the code located at `CMProcessing` followed by `pb_tool deploy --config_file pb_tool_win.cfg` and then at QGIS `Plugins` > `Plugin Reloader` > `Snow Melt runoff modelling Data Pre-Processing` should reload the plugin incorporating new changes accordingly.

# Project Structure
```
SMProcessing/
|--tests/                   # Tests for plugin, yet to be written.
|--core/                    # Directory containing logic behind the
|  |                        #   processing.
|  |--DEMProcessing.py      # Code defining the logic for DEM related
|  |                        #   processing functions.
|  |--LSTProcessing.py      # Code defining the logic for LST related
|                           #   processing functions
|--SMProcessing.py          # Main Script which has functions to
|                           #   add plugin into menu, run the 
|                           #   plugin when clicked etc.
|--SMProcessing_dialog.ui   # .ui file, to be opened using Qt Creator
|                           #   used to define the layout of plugin.
|--SMProcessing_dialog.py   # Contains class which defined the UI,
|                           #   and the object of which can be used to
|                           #   interact with the UI during runtime.
|--utils.py                 # To contain global utility functions.
|--pb_tool_win.cfg          # Config file for pb_tool (windows).
|--pb_tool-ubuntu.cfg       # Config file for pb_tool (ubuntu).
|                           #   These files should be changed according
|                           #   to the configuration of QGIS install. 
|--metadata.txt             # Contains metadata about the plugin.
|--__REST__                 # Either Self-Explanatory or Unimportant
```

# My Understanding of the code (@pritamd47)
## Important files and what they do
- `./SMProcessing.py` - It is the _main_ file where the execution starts. It contains the class `SMProcessing`.
    - `class SMProcessing` - Takes in an `iface` argument, which is a [QgisInterface](https://qgis.org/pyqgis/3.4/gui/QgisInterface.html#qgis.gui.QgisInterface) object.
       It initialises initialises the Plugin Directory, adds the Plugin to `Plugin` dropdown menu (`add_action` and `initGui`), defines `unload` which removes the plugin from menu (probably used when closing QGIS), and the main function which is run when the menu item is clicked - `run`. <br>
       The `run` function is called when the menu item is clicked. This initializes an `SMProcessingDialog` instance, which is the GUI of the plugin.
- `./SMProcessing_dialog.py` - Defines the Class of the GUI Dialog, `SMProcessingDialog`.
    - `class SMProcessingDialog` - Inherits from `QtWidgets.QDialog` and `FORM_CLASS`. It the the class of the main dialog that is loaded when the menu item is clicked. It loads the layer information in the input placeholders (here, combo-boxes). + It provides functions to interact with the plugin, `logMessage(...)` using which text can be appended to the `outputPane` which is to act as a logging interface.  
- `.core/DEMProcessing` - Will handle all the logic of DEM Processing, and the Dialog will merely wrap around the logical functions defined in this class.
- `./utils.py` - To define some global functions which make life easier. Example of such a function would be something like `print_`, which will work exactly like the standard `print` function, but will output the arguments passed to various streams (`QgsMessageLog`, `outputPane` and `Qgis console`).

# Important Links
 - For information on writing PyQGIS code, see <b>http://loc8.cc/pyqgis_resources</b> for a list of resources.
 - [An old resource — some stuff mentioned here is obsolete — but still is a good reference as a starting guide. I followed these steps to create the initial files for the Plugin](https://www.qgistutorials.com/en/docs/building_a_python_plugin.html)
 - [PyQGIS Cookbook. Snippets explaining how stuff works](https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/)
 - [PyQGIS in a day – Good resource to look for some misc. stuff](https://courses.spatialthoughts.com/pyqgis-in-a-day.html#qt)
 - [GeoAPIs combines multiple API documentations in a fast, organized, and searchable interface](http://geoapis.sourcepole.com/)


&copy;2011-2019 GeoApt LLC - geoapt.com 
