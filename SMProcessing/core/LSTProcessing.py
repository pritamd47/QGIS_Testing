from .utils import linear_regression
from osgeo import gdal
from osgeo import osr
import pandas as pd
import numpy as np
import numpy.ma as ma

class LSTProcessing:
    def __init__(self, files, DEM):
        """
        Args:
            files{list}: list of file paths to rasters
            DEM{DEMProecssing Object}: A DEMProcessing object pointing to the
                                       DEM file
        """
        self.files = files

        self.dem_path = DEM.path
        # self.gdalDEM = gdal.Open(self.dem_path)
        # self.DEM = gdalDEM.band(1).astype(np.float64)
        self.DEM = DEM.as_array()
        # self.DEM[self.DEM == DEM.nodata] = np.nan
        self.DEM_crs = DEM.crs

        self.lapse_rate_table = None

    def calc_lapse_rate(self, lst_band=1):
        """Given some files, this function will calculate the lapse rate for
        all the files and return a pandas dataframe containing the slope and
        intercept.

        Args:
            lst_band: the band which contains LST data
        Returns:
            lapse_rate_table: pandas data-frame containing the coefficients
        """
        # FIXME DOesn't work. Might need sklearn
        values = []
        for path in self.files:
            gdalLST = gdal.Open(path)
            gdalBand = gdalLST.GetRasterBand(lst_band)
            proj = osr.SpatialReference(wkt=gdalLST.GetProjection())
            proj = ":".join(("EPSG", proj.GetAttrValue('AUTHORITY',1)))

            LST = gdalBand.ReadAsArray()

            if self.DEM.shape != LST.shape:
                raise ValueError(f"Shapes do not match: "
                                 f"DEM--{self.DEM.shape} LST--{LST.shape}")
            if self.DEM_crs != proj:
                raise ValueError(f"CRS doesn't match. Convert to same CRS"
                                 f"DEM--{self.DEM_crs} LST--{proj}")

            # LST[LST == gdalBand.GetNoDataValue()] = np.nan
            LST_masked = ma.array(
                LST,
                mask=(LST == gdalBand.GetNoDataValue())
            )

            DEM_masked = self.DEM.copy()

            # Remove where either of the masks exist
            combined_mask = DEM_masked.mask | LST_masked.mask

            # Set this new mask to LST and DEM
            LST_masked.mask = combined_mask
            DEM_masked.mask = combined_mask

            flattened_mask = combined_mask.flatten()
            LST_flattened = LST_masked.flatten()[~flattened_mask].data
            DEM_flattened = DEM_masked.flatten()[~flattened_mask].data

            c, m = linear_regression(DEM_flattened, LST_flattened)

            values.append({
                'file': path,
                'dem': self.dem_path,
                'c': c,
                'm': m
            })
        self.lapse_rate_table = pd.DataFrame(values)
        return self.lapse_rate_table
