# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SMProcessingDialog.py
 
 This file should handle the UI of the main window.
 

                                 A QGIS plugin
 This plugin helps in pre-processing data for Snow Melt runoff modelling
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2020-01-24
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Pritam Das
        email                : pritamd47@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import re

from qgis.PyQt import (
    QtWidgets,
    uic
)
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer
)

from .core.utils import print_
from .core.DEMProcessing import DEMProcessing
from .core.LSTProcessing import LSTProcessing
from .core.SnowProcessing import SnowProcessing

# This loads your .ui file so that PyQt can populate your plugin with the
# elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'SMProcessing_dialog_base.ui'))


class SMProcessingDialog(QtWidgets.QDialog, FORM_CLASS):
    """[summary]
    
    Arguments:
        QtWidgets {[type]} -- [description]
        FORM_CLASS {[type]} -- [description]
    """

    # FIXME A problem which is currently apparent is that, since there is no
    #  way to 'group' the actions/inputs together (although the tabbed view is
    #  visually grouped, it is not grouped logically. So find a way around this
    #  problem. Either having different Dialogs for different workflows -- or
    #  maybe partition the logic into different files, keeping the main dialog
    #  in this file. BRAINSTORM
    def __init__(self, iface_obj,
                 parent=None):  # TODO Add description of iface_obj

        """Constructor."""
        super(SMProcessingDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.iface = iface_obj
        self.layersDict = None
        self.DEM = None
        self.SEPARATOR = lambda: self.log_message("-" * 10)
        self.terra_file_paths = None
        self.aqua_file_paths = None
        self.DEM_path = None

        # Populate the Combo Boxes
        self.populate_inputs()

        self.log_message("*Output-Pane*. Results will be shown here.")

        # Connecting functions with buttons
        # DEM
        self.CalculateStats_Button.clicked.connect(self.on_calc_stats)
        self.Classify_Button.clicked.connect(self.on_classify)
        self.Intersect_Button.clicked.connect(self.on_intersect)
        self.ExportUniqueVals_Button.clicked.connect(self.on_export_uniques)
        # LST
        self.LST_BrowseWorkingDirectoryButton.clicked.connect(self.on_browse_LST)
        self.LST_LoadRasterButton.clicked.connect(self.on_load_raster_LST)
        self.LST_LoadRastersButton.clicked.connect(self.on_load_rasters_LST)
        self.LST_RemoveRasterButton.clicked.connect(self.on_remove_raster_LST)
        self.LST_ClearAllButton.clicked.connect(self.on_clear_all_LST)
        self.LST_CalculateLapseRateButton.clicked.connect(self.on_calc_lapse_rate)
        # Snow
        self.Snow_BrowseWorkingDirectoryButton.clicked.connect(self.on_browse_Snow)
        self.Snow_LoadRasterButton.clicked.connect(self.on_load_raster_Snow)
        self.Snow_LoadRastersButton.clicked.connect(self.on_load_rasters_Snow)
        self.Snow_RemoveRasterButton.clicked.connect(self.on_remove_raster_Snow)
        self.Snow_ClearAllButton.clicked.connect(self.on_clear_all_Snow)
        self.Snow_LoadTerraFromSelectionButton.clicked.connect(
            self.on_load_terra_files_from_selection
        )
        self.Snow_LoadAquaFromSelectionButton.clicked.connect(
            self.on_load_aqua_files_from_selection
        )
        self.Snow_DEMButton.clicked.connect(self.on_load_DEM)
        self.Snow_OutputDirectoryButton.clicked.connect(self.on_load_output_directory)
        self.Snow_Step1Button.clicked.connect(self.on_step1)
        self.Snow_Step2Button.clicked.connect(self.on_step2)
        self.Snow_Step3Button.clicked.connect(self.on_step3)

        # Connecting Qgis Events
        QgsProject.instance().layersAdded.connect(self.populate_inputs)

        # Create DEM Object when ComboBox updates
        self.DEM_ComboBox.activated.connect(self.on_dem_update)

        self.Close.clicked.connect(self.on_close)

    def populate_inputs(self):
        """Populates the dialog box with information from QGIS Project
            If there are no loaded layers, will do nothing.
        """
        # TODO Add a way to handle the IDs and names (and if possible, the
        #  QgsLayer objects) so that IDs can be used to extract any instance of
        #  any layer. Currently it is handled by a dict. Not ideal.
        self.layersDict = QgsProject.instance().mapLayers()

        print("length: ", self.layersDict, len(self.layersDict))

        if len(self.layersDict) is not 0:
            # Clear previous contents to ensure no duplicates
            self.DEM_ComboBox.clear()
            # self.AdditionalRaster_ComboBox.clear()
            # self.ElevationZone_ComboBox.clear()

            vectors = []
            rasters = []

            for key in self.layersDict:
                if isinstance(self.layersDict[key], QgsVectorLayer):
                    vectors.append(self.layersDict[key].name())
                elif isinstance(self.layersDict[key], QgsRasterLayer):
                    rasters.append(self.layersDict[key].name())
                else:
                    print_("Layer is neither Raster nor Vector: ", id)

            # Add the Rasters to comboboxes accepting rasters
            self.DEM_ComboBox.addItems(rasters)
            # self.AdditionalRaster_ComboBox.addItems(rasters)

            # Add the vectors to comboboxes accepting vectors
            # self.ElevationZone_ComboBox.addItems(vectors)

            # Define DEM
            if self.DEM_ComboBox.currentText() is not None:
                self.DEM = DEMProcessing(
                    self.getLayerObj(
                        self.DEM_ComboBox.currentText()
                    )
                )
            else:
                self.DEM = None
        else:
            print("No Layers loaded")

    def getLayerObj(self, id_, type_='ID'):
        """
        Get the Layer object (QgsRasterLayer or QgsVectorLayer) by name or ID
        or path.
        Args:
            id_: Identifier for the layer -- to be defined by `type`
            type_: String defining the type of ID it is. Can be any of these:
                    - ID     -- str: Layer ID
                    - NAME   -- str: Layer name (Avoid this)
                    - SOURCE -- str: layer Source
        Returns:
            Layer: QgsRasterLayer OR QgsVectorLayer depending on the type of
                    layer identified by the ID
        """
        # FIXME While this works as of now, when multiple rasters of same are
        #  present in the project, it create a conflict and only the first
        #  layer is selected.

        # `.mapLayersByName()` returns a list of objects. Select the first
        #   object.
        layer = QgsProject.instance().mapLayersByName(id_)[0]
        return layer

    def on_dem_update(self):
        layer_name = self.DEM_ComboBox.currentText()
        try:
            self.DEM = DEMProcessing(self.getLayerObj(layer_name))
        except Exception as e:
            self.log_message(e)

    def on_calc_stats(self):
        """Wrapper to calculate statistics of the DEM file and show the results
        """
        self.SEPARATOR()
        if self.DEM is not None:
            result = self.DEM.calc_stats()
            self.log_message("Statistics Results: ")
            self.log_message(result)
        else:
            self.log_message("DEM layer not selected!")

    def on_classify(self):
        """Classify DEM using further options or inbuilt processing
           option.
        """
        self.SEPARATOR()
        print("Classifying started")
        result, save_path = self.DEM.classify()
        self.log_message(f"Classify Results:")
        self.log_message(f"Classifying Finished, and saved at: {save_path}")
        self.log_message(result)
        self.load_raster(save_path, "Classify Result")

    def on_intersect(self):
        """Zonal Intersection between elevation zones and DEM
        """
        pass  # Todo add code

    def on_export_uniques(self):
        """Export unique values
        """
        self.SEPARATOR()
        if self.DEM is not None:
            self.log_message("Export Uniques Report:")
            results = self.DEM.export_uniques()
            self.log_message(results)
        else:
            self.log_message("ERROR: DEM file not chosen.")

    # LST and Functions
    def on_browse_LST(self, start="."):
        """Opens a dialog box for selection of directory
        """
        dialog = QtWidgets.QFileDialog(self, 'Select Working Directory')
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            fname = dialog.selectedFiles()[0]
            self.log_message(f"Selected Directory: {fname}")
            self.LST_WorkingDirectoryLineEdit.setText(fname)

    def on_load_raster_LST(self):
        """Open a dialog to load rasters individually
        """
        dialog = QtWidgets.QFileDialog(self, 'Select Raster')
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            fnames = dialog.selectedFiles()
            if len(fnames) == 1:
                self.log_message(f"{len(fnames)} file loaded")
            else:
                self.log_message(f"{len(fnames)} files loaded")
            self.LST_FilesList.addItems(fnames)

    def on_load_rasters_LST(self):
        """Loads rasters based on the selected directory and regex expression
        """
        working_directory_path = self.LST_WorkingDirectoryLineEdit.text()
        self.SEPARATOR()
        if working_directory_path is '':
            self.log_message("Error: No Directory chosen")
            return
        elif self.LST_FileSelectionRegexLineEdit.text():
            re_txt = self.LST_FileSelectionRegexLineEdit.text()
            self.log_message(f"Regex: {re_txt}")
            files = ['/'.join((working_directory_path, x))
                     for x in os.listdir(working_directory_path)
                     if re.search(re_txt, x)]
        else:
            self.log_message(
                "No regex defined: Loading files ending with '.tif'"
            )
            files = ['/'.join((working_directory_path, x))
                     for x in os.listdir(working_directory_path)
                     if x.endswith('.tif') or x.endswith('.tiff')]

        if len(files) == 1:
            self.log_message(f"{len(files)} file loaded")
        else:
            self.log_message(f"{len(files)} files loaded")
        self.LST_FilesList.addItems(files)

    def on_remove_raster_LST(self):
        """This function will remove the selected item from the Files list
        """
        selected = self.LST_FilesList.selectedItems()
        if selected:
            for item in selected:
                self.LST_FilesList.takeItem(self.LST_FilesList.row(item))
                self.log_message(f"Removed: {item.text()}")
        else:
            self.log_message("Select a raster to remove")

    def on_clear_all_LST(self):
        """Clear the list of files
        """
        self.log_message(f"Clearing all loaded files")
        self.LST_FilesList.clear()

    def on_calc_lapse_rate(self):
        itemsTextList = [str(self.LST_FilesList.item(i).text()) for i in
                         range(self.LST_FilesList.count())]
        LSTProcessor = LSTProcessing(itemsTextList, self.DEM)
        results = LSTProcessor.calc_lapse_rate()
        self.log_message(results.loc[:, ('m', 'c')])

        # Save the results
        working_directory_path = self.LST_WorkingDirectoryLineEdit.text()
        save_path = '/'.join((working_directory_path, "Lapse_rate.csv"))
        results.to_csv(save_path)
        self.log_message(f"Calculation complete -- "
                         f"saving results at: {save_path}")

    # Snow functions
    def on_browse_Snow(self, start="."):
        """Opens a dialog box for selection of directory
        """
        dialog = QtWidgets.QFileDialog(self, 'Select Working Directory')
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            fname = dialog.selectedFiles()[0]
            self.log_message(f"Selected Directory: {fname}")
            self.Snow_WorkingDirectoryLineEdit.setText(fname)

    def on_load_raster_Snow(self):
        """Open a dialog to load rasters individually
        """
        dialog = QtWidgets.QFileDialog(self, 'Select Raster')
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            fnames = dialog.selectedFiles()
            if len(fnames) == 1:
                self.log_message(f"{len(fnames)} file loaded")
            else:
                self.log_message(f"{len(fnames)} files loaded")
            self.Snow_FilesList.addItems(fnames)

    def on_load_rasters_Snow(self):
        """Loads rasters based on the selected directory and regex expression
        """
        working_directory_path = self.Snow_WorkingDirectoryLineEdit.text()
        self.SEPARATOR()
        if working_directory_path is '':
            self.log_message("Error: No Directory chosen")
            return
        elif self.Snow_FileSelectionRegexLineEdit.text():
            re_txt = self.Snow_FileSelectionRegexLineEdit.text()
            self.log_message(f"Regex: {re_txt}")
            files = ['/'.join((working_directory_path, x))
                     for x in os.listdir(working_directory_path)
                     if re.search(re_txt, x)]
        else:
            self.log_message(
                "No regex defined: Loading files ending with '.tif'"
            )
            files = ['/'.join((working_directory_path, x))
                     for x in os.listdir(working_directory_path)
                     if x.endswith('.tif') or x.endswith('.tiff')]

        if len(files) == 1:
            self.log_message(f"{len(files)} file loaded")
        else:
            self.log_message(f"{len(files)} files loaded")
        self.Snow_FilesList.addItems(files)

    def on_remove_raster_Snow(self):
        """This function will remove the selected item from the Files list
        """
        selected = self.Snow_FilesList.selectedItems()
        if selected:
            for item in selected:
                self.Snow_FilesList.takeItem(self.Snow_FilesList.row(item))
                self.log_message(f"Removed: {item.text()}")
        else:
            self.log_message("Select a raster to remove")

    def on_clear_all_Snow(self):
        """Clear the list of files
        """
        self.log_message(f"Clearing all loaded files")
        self.Snow_FilesList.clear()

    def on_load_terra_files_from_selection(self):
        self.terra_file_paths = [str(self.Snow_FilesList.item(i).text())
                                 for i in range(self.Snow_FilesList.count())]
        self.Snow_TerraStatusLabel.setText(
            f'Loaded {len(self.terra_file_paths)} files -- Terra'
        )
        self.log_message(f'Loaded {len(self.terra_file_paths)} files -- Terra')

    def on_load_aqua_files_from_selection(self):
        self.aqua_file_paths = [str(self.Snow_FilesList.item(i).text())
                                for i in range(self.Snow_FilesList.count())]
        self.Snow_AquaStatusLabel.setText(
            f'Loaded {len(self.aqua_file_paths)} files -- Aqua'
        )
        self.log_message(f'Loaded {len(self.aqua_file_paths)} files -- Aqua')

    def on_load_DEM(self):
        dialog = QtWidgets.QFileDialog(self, 'Select DEM')
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            fname = dialog.selectedFiles()[0]
            self.DEM_path = fname
            self.Snow_DEMLineEdit.setText(fname)

    def on_load_output_directory(self):
        dialog = QtWidgets.QFileDialog(self, 'Select Output Directory')
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            fname = dialog.selectedFiles()[0]
            self.log_message(f"Selected Output Directory: {fname}")
            self.Snow_OutputDirectoryLineEdit.setText(fname)

    def on_step1(self):
        working_directory_path = self.Snow_OutputDirectoryLineEdit.text()
        self.log_message(f"Starting Step-1 of cloud removal")
        Snow_processor = SnowProcessing(
            self.terra_file_paths,
            self.aqua_file_paths,
            working_directory_path
        )
        Snow_processor.step_1()

    def on_step2(self):
        working_directory_path = self.Snow_OutputDirectoryLineEdit.text()
        self.log_message(f"Starting Step-2 of cloud removal")
        Snow_processor = SnowProcessing(
            self.terra_file_paths,
            self.aqua_file_paths,
            working_directory_path
        )
        Snow_processor.step_2()

    def on_step3(self):
        working_directory_path = self.Snow_OutputDirectoryLineEdit.text()
        self.log_message(f"Starting Step-3 of cloud removal")
        Snow_processor = SnowProcessing(
            self.terra_file_paths,
            self.aqua_file_paths,
            working_directory_path,
            self.DEM_path
        )
        Snow_processor.step_3()

    def log_message(self, text):
        """Pass on messages passed as `text` to the OutputPane

        Args:
            text: Message to log as String
        """
        if isinstance(text, dict):  # If dict, print consecutive key
            to_text = []  # and value on consecutive lines
            for key in text:
                to_text.append(f"{key}: {text[key]}")
            text = '\n'.join(to_text)
        elif not isinstance(text, str):  # If neither dict nor str, convert
            text = str(text)  # to string

        self.outputPane.appendPlainText(f"{text}")
        print(f"{text}")

    def load_raster(self, path, name):
        layer = QgsRasterLayer(path, name)
        if not layer.isValid():
            self.log_message(f"Failed to load raster: {path}")
            return None
        return layer

    def on_close(self):
        self.outputPane.clear()
        self.close()

