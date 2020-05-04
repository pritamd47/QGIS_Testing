from osgeo import gdal, gdal_array, osr
import numpy as np
import numpy.ma as ma
import tempfile
import os
import re
from shutil import copyfile
import math

gdal.UseExceptions()

class Raster:
    def __init__(self, path=None):
        self.rast = None
        self.profile = dict()

        self._gdal_rast = None
        self._gdal_band = None

        if path is not None:
            self.path = path
            self.read()
        else:
            self.path = None

    def read(self):
        print(f"Reading file: {self.path}")
        self.rast, self._gdal_rast, self._gdal_band = self._read()
        self.profile.update(self._read_profile())

    def _read(self):
        raster = gdal.Open(self.path)

        band = raster.GetRasterBand(1)
        nodata = band.GetNoDataValue()
        arr = band.ReadAsArray()
        masked_raster = ma.masked_equal(arr, nodata)

        return masked_raster, raster, band

    def _read_profile(self):
        profile = dict()

        # Add code to update profile. Profile is a dict containing various
        #   information about the raster. Such as the shape, no data value etc
        if not self._gdal_rast:
            raise Exception("Raster not found")
        if not self._gdal_band:
            raise Exception("Band not found")

        profile['driver'] = "GTiff"
        profile['nodata'] = self._gdal_band.GetNoDataValue()
        profile['path'] = self.path
        profile['dtype'] = self._nptype_to_gdaltype(self.rast.data.dtype)
        profile['geotransform'] = self._gdal_rast.GetGeoTransform()
        profile['proj'] = self._gdal_rast.GetProjectionRef()
        profile['shape'] = self.rast.shape
        profile['cols'] = self._gdal_rast.RasterXSize
        profile['rows'] = self._gdal_rast.RasterYSize
        profile['name'] = re.split(r'[/\\]', self.path)[-1].rstrip('.tif')

        return profile

    def _nptype_to_gdaltype(self, t):
        return gdal_array.NumericTypeCodeToGDALTypeCode(t)

    def array_to_rast(self, array, profile, path=None):
        self.profile = profile
        self.path = path

        if path is None:
            f = tempfile.NamedTemporaryFile(suffix='.tif')
            path = f.name

        driver = gdal.GetDriverByName(self.profile['driver'])

        out_raster = driver.Create(
            path,
            self.profile['cols'],
            self.profile['rows'])

        out_raster.SetGeoTransform(self.profile['geotransform'])
        out_band = out_raster.GetRasterBand(1)
        out_band.SetNoDataValue(profile['nodata'])
        out_band.WriteArray(array)

        out_rast_SRS = osr.SpatialReference()
        # FIXME Allow other EPSGs to be used as spatial reference
        out_rast_SRS.ImportFromEPSG(4326)
        out_raster.SetProjection(out_rast_SRS.ExportToWkt())

        self._gdal_rast = out_raster
        self._gdal_band = out_band

        return out_raster

    def write(self):
        print(f'Writing at: {self.path}')
        self._gdal_band.FlushCache()

        # if path is None and self.path is None:
        #     raise Exception("Path not defined")
        # elif path is None and self.path is not None:
        #     print(f'Writing at: {self.path}')
        #     self._gdal_band.FlushCache()
        #     return self.path
        # FIXME Add functionality of path. Path can be chosen, such that the
        #  result can be saved by passing path parameter

    def _generate_temp_file_path(self):
        # For creating rasters temporarily, before saving it permanently in
        #  some other location
        temp_dir = tempfile.TemporaryDirectory(dir='.')
        temp_filepath = os.path.join(
            temp_dir.name,
            f"{next(tempfile._get_candidate_names())}.tif"
        )

        return temp_filepath

    def __del__(self):
        del self.rast

class SnowProcessing:
    def __init__(self, terra_files, aqua_files, working_directory, dem_path=None):
        self.working_directory = working_directory

        self.terra_files = terra_files
        self.aqua_files = aqua_files

        self.dem_path = dem_path

    def step_1(self):
        # Check integrity of files
        if len(self.terra_files) != len(self.aqua_files):
            raise Exception(
                f"Number of aqua and terra files are not same"
                f"{len(self.aqua_files)} vs. {len(self.terra_files)}")

        savedir = os.path.join(self.working_directory, 'step1')
        if not os.path.isdir(savedir):
            os.mkdir(savedir)

        for terra_path, aqua_path in zip(self.terra_files, self.aqua_files):
            terra = Raster(terra_path)
            aqua = Raster(aqua_path)

            terra_arr = terra.rast.data
            aqua_arr = aqua.rast.data

            corrected = np.empty(terra_arr.shape)
            corrected[:] = np.nan

            corrected = np.maximum(terra_arr, aqua_arr)

            profile = terra.profile
            profile.update(dtype=np.float64)

            result = Raster()
            savepath = os.path.join(
                savedir,
                f"{terra.profile['name']}_"
                f"{aqua.profile['name']}_"
                f"combined.tif")

            result.array_to_rast(corrected, profile, savepath)
            result.write()
            del result

        return savedir

    def step_2(self):
        step1_directory = self.step_1()

        files = [os.path.join(step1_directory, f)
                 for f in os.listdir(step1_directory)
                 if f.endswith('.tif')]
        savedir = os.path.join(self.working_directory, "step2")
        if not os.path.isdir(savedir):
            os.mkdir(savedir)

        for current_index in range(0, len(files)):
            print(f"{current_index} -> {files[current_index]}")

            if current_index == 0 or current_index == len(files)-1:
                current = Raster(files[current_index])

                result_arr = current.rast.data

                savepath = os.path.join(
                    savedir,
                    f"{current.profile['name']}.tif")
                print(savepath)

                result = Raster()
                result.array_to_rast(result_arr, current.profile, savepath)
                result.write()
                del result
            elif current_index == 1 or current_index == len(files)-2:
                previous = Raster(files[current_index-1])
                current = Raster(files[current_index])
                next_ = Raster(files[current_index+1])

                previous_arr = previous.rast.data
                current_arr = current.rast.data
                next_arr = next_.rast.data

                result_arr = current_arr.copy()

                snow_condition = ((current_arr == 1) | (current_arr == 0)) \
                                 & (previous_arr==3) \
                                 & (next_arr==3)
                result_arr[snow_condition] = 3

                nosnow_condition = ((current_arr==1) | (current_arr==0)) \
                                   & (previous_arr==2) \
                                   & (next_arr==2)
                result_arr[nosnow_condition] = 2

                savepath = os.path.join(
                    savedir,
                    f"{current.profile['name']}.tif")

                result = Raster()
                result.array_to_rast(result_arr, current.profile, savepath)
                result.write()
                del result
            else:
                previous_2 = Raster(files[current_index-2])
                previous = Raster(files[current_index-1])
                current = Raster(files[current_index])
                next_ = Raster(files[current_index+1])
                next_2 = Raster(files[current_index+2])

                previous_2_arr = previous_2.rast.data
                previous_arr = previous.rast.data
                current_arr = current.rast.data
                next_arr = next_.rast.data
                next_2_arr = next_2.rast.data

                result_arr = current_arr.copy()

                # If Cloud or Nodata in current band, and 3 or 2 in prev and
                # next, replace current by the prev/next value
                snow_condition = ((current_arr==1)|(current_arr==0)) \
                                 & (previous_arr==3) \
                                 & (next_arr==3)
                result_arr[snow_condition] = 3

                nosnow_condition = ((current_arr==1)|(current_arr==0)) \
                                   & (previous_arr==2) \
                                   & (next_arr==2)
                result_arr[nosnow_condition] = 2

                # If cloud or nodata in current band, and 3 or2 in prev2 and
                # next, replace current by theprev/next value
                snow_condition = ((current_arr==1)|(current_arr==0)) \
                                 & (previous_2_arr==3) \
                                 & (next_arr==3)
                result_arr[snow_condition] = 3

                nosnow_condition = ((current_arr==1)|(current_arr==0)) \
                                   & (previous_2_arr==2) \
                                   & (next_arr==2)
                result_arr[nosnow_condition] = 2

                # If cloud or nodata in current band, and 3 or 2 in prev and
                # next 2, replace current by theprev/next value
                snow_condition = ((current_arr==1)|(current_arr==0)) \
                                 & (previous_arr==3)\
                                 & (next_2_arr==3)
                result_arr[snow_condition] = 3

                nosnow_condition = ((current_arr==1)|(current_arr==0)) \
                                   & (previous_arr==2) \
                                   & (next_2_arr==2)
                result_arr[nosnow_condition] = 2

                savepath = os.path.join(
                    savedir,
                    f"{current.profile['name']}.tif")

                result = Raster()
                result.array_to_rast(result_arr, current.profile, savepath)
                result.write()
                del result
        return savedir

    def step_3(self):
        if self.dem_path is None:
            raise NameError("DEM Path not specified")

        step2_dir = self.step_2()

        files = [os.path.join(step2_dir, f)
                 for f in os.listdir(step2_dir)
                 if f.endswith('.tif')]
        savedir = os.path.join(self.working_directory, "step3")
        if not os.path.isdir(savedir):
            os.mkdir(savedir)

        dem_file = Raster(self.dem_path)
        dem_arr = dem_file.rast.data

        elevations = np.arange(
            math.floor(dem_arr.min()),
            math.ceil(dem_arr.max()+1),
            step=5
        )
        reversed_elevations = elevations[::-1]

        for file_path in files:
            # with rasterio.open(file_path) as rst:
            rst = Raster(file_path)
            band = rst.rast.data

            # Check if the raster has >70% cloud-free
            uniques, counts = np.unique(band, return_counts=True)
            nums = dict(zip(uniques, counts))
            if 1 not in nums.keys():
                nums[1] = 0
            cloud_percentage = (nums[1]/(band.shape[0] * band.shape[
            1]))*100
            if cloud_percentage < 70:
                for i, elevation in enumerate(elevations):
                    masked_raster = np.where(
                        dem_arr <= elevation,
                        band,
                        np.nan
                    )

                    if 3 in masked_raster:
                        # First Snow found; This will be the minimum elevation
                        # For every cell below this elevation, if there is
                        # cloud, mark that cell as Non-snow

                        band[(dem_arr <= elevation) & (band == 1)] = 2
                        break
                    else:
                        continue

                for i, elevation in enumerate(reversed_elevations):
                    masked_raster = np.where(dem_arr >= elevation,
                    band, np.nan)

                    if 2 in masked_raster:
                        # First Non-Snow found; This will be the maximum
                        # elevation For every cell above this elevation, if
                        # there is cloud, mark that cell as snow

                        band[(dem_arr >= elevation) & (band == 1)] = 3
                        break
                    else:
                        continue

                savepath = os.path.join(
                    savedir,
                    f"{rst.profile['name']}.tif")
                print(f"Current File: {rst.profile['name']}.tif -- "
                      f"Cloud Percentage: {cloud_percentage}")

                result = Raster()
                result.array_to_rast(band, rst.profile, savepath)
                result.write()
                del result
            else:
                # save the same raster
                savepath = os.path.join(
                    savedir,
                    f"{rst.profile['name']}.tif")

                print(f"Skipped File: {rst.profile['name']}.tif -- "
                      f"Cloud Percentage: {cloud_percentage}")
                copyfile(file_path, savepath)

        return savedir


def main():
    aqua_dir = r"F:\Dissertation\temp\modis-daily-data\Aqua-classified"
    terra_dir = r"F:\Dissertation\temp\modis-daily-data\Terra-classified"
    working_dir = r"F:\Dissertation\temp\modis-daily-data"

    SP = SnowProcessing(terra_dir, aqua_dir, working_dir)
    SP.step_1()

if __name__ == '__main__':
    main()