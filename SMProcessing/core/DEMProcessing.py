from qgis import processing
import os
import numpy as np
from osgeo import gdal
import numpy.ma as ma

class DEMProcessing:
    """
    Logic Behind DEM Processing
    """
    def __init__(self, raster):
        """
        Args:
            raster: QgsRasterLayer object pointing to the DEM raster.
        """
        self.raster = raster
        self.path = self.raster.source()
        self.working_directory, self.file_name = os.path.split(self.path)
        self.crs = self.raster.crs().authid()

        self.gdalRast = gdal.Open(self.path)
        self.gdalBand = self.gdalRast.GetRasterBand(1)

        self.nodata = self.gdalBand.GetNoDataValue()

        # If machine is windows, change '/' to '\\'
        if os.name is 'nt':
            self.working_directory = self.working_directory.replace('/', '\\')

        print(self.working_directory)
        # self.band = rast_to_arr(self.raster)

    def calc_stats(self):
        """
        Calculate and return basic statistics about the DEM raster.
            Algorithm: `qgis:rasterlayerstatistics`
        Returns:
            result {Dict}: {
                                'Mean': Mean,
                                'Max': Max,
                                'Min': Min,
                                'Std_dev': Standard Deviation,
                                ...
                            }
        """
        alg_string = "qgis:rasterlayerstatistics"
        # Prepare Parameters
        params = {
            "INPUT": self.raster,
            "BAND": 1  # 1 for now.
        }  # TODO Add functionality to choose band

        result = processing.run(alg_string, params)

        return result

    def export_uniques(self):
        """
        Return the unique values in a raster using QGIS native processing
        algorithm.

        Algorithm: native:rasterlayeruniquevaluesreport
        ----Inputs: INPUT:              Input raster layer
                    BAND:               Raster Band
                    OUTPUT_HTML_FILE:   (optional) Defaults to temporary file
                    OUTPUT_TABLE:       (optional) Defaults to skip
        Returns:
        ----Result {Dict}:
            {
                'CRS_AUTHID': CRS as string,
                'EXTENT': Extent,
                'HEIGHT_IN_PIXELS': Height in Pix,
                'NODATA_PIXEL_COUNT': No Data Count,
                'OUTPUT_HTML_FILE': Path to HTML file with results,
                'TOTAL_PIXEL_COUNT': Total Pixels,
                'WIDTH_IN_PIXELS': 1891
            }
        """
        alg_string = "native:rasterlayeruniquevaluesreport"
        params = {
            "INPUT": self.raster,
            "BAND": 1,  # TODO add functionality to choose band
            "OUTPUT_TABLE": os.path.join(self.working_directory, "uniques.csv")
        }
        result = processing.run(alg_string, params)
        return result

    def classify(self):
        """
        Will use the algorithm provided by GRASS: grass7:r.reclass
        TODO Add a check while starting the plugin to see if QGIS has been
             loaded with GRASS or not. If yes, then classify will run, or it
             will show a warning.

        Resource: https://grass.osgeo.org/grass78/manuals/r.reclass.html

        The main part of this algorithm is definition of rules. Rules are
        defined using `txtrules` which will be a string containing rules.

        Rules:
            old_value_1 old_value_2              = new_value label # Individual
            old_value_4 thru old_value_5         = new_value label # Range

        The new lines must be added explicitly in the string

        Example:
            -------------------------
            *            = NULL
            100 25 10    = 1 Snow
            150 thru 250 = 2 Non Snow
            -------------------------
            Will mark the pixels of value 100, 25 and 10 as 1 and label as snow
            and the pixels with value in between 150 and 250 will be
            represented by the value 2 and label as Non Snow.

        Algorithm: grass7:r.reclass
        ----Inputs: input               Input Raster Layer
                    txtrules            String containing rules
                    output              Path of output. Either Memory or Disk
        Returns:
        ---- (Dict)
        {
            'output': QgsProcessingOutputLayerDefinition  # path to output is
                                                            stored as `sink`
        }
        """

        # The plan is to create a dummy classify function, which will classify
        #   the DEM in equal intervals for now. Later update the logic, adding
        #   more functionality.
        # TODO Add functionality. Currently only Equal Interval
        stats = self.calc_stats()
        min, max = stats['MIN'], stats['MAX']

        intervals = 10  # Arbitrary
        breaks = np.linspace(min, max, intervals)
        txt_rules = f""
        for i in range(len(breaks) - 1):
            pair = breaks[i], breaks[i + 1]
            txt_rules = txt_rules + f"\n{pair[0]} thru {pair[1]} = {i}"

        alg_string = "grass7:r.reclass"
        # Create parameters, saving the classified output raster at the
        #   directory containing the raster
        save_path = os.path.join(self.working_directory, "classified.tiff")
        params = {
            'input': self.raster,
            'output': save_path,
            'txtrules': txt_rules
        }

        result = processing.runAndLoadResults(alg_string, params)
        return result, save_path

    def as_array(self, band=1):
        """Return the band array as a numpy array object
        Args:
            band: Which band to return as array
        Returns:
            band_result {numpy array}: 2D numpy array containing band
                                       information
            rast.nodata: no-data value
        """
        # FIXME make use of masked array instead of converting to float.
        #   some weird bug related to conversion. CODE IS BROKEN
        b = self.gdalRast.GetRasterBand(band)
        band_array = b.ReadAsArray()
        band_masked = ma.array(
            band_array,
            mask=(band_array == b.GetNoDataValue())
        )

        return band_masked
