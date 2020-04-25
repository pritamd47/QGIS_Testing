import unittest

from qgis.PyQt import (
        QtWidgets,
        uic
    )
    
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer
)

from SMProcessing.core import DEMProcessing

class TestInit(unittest.TestCase):
    def test_io(self):
        self.DEMProcessor = DEMProcessing.DEMProcessing(QgsRasterLayer("reclassify_aster.tif"))
        self.assertEqual(type(self.DEMProcessor.raster), "QgsRasterLayer")

if __name__ == "__main__":
    unittest.main()