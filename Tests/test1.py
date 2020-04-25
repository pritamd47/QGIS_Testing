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

from SMProcessing.SMProcessing import SMProcessing
from .utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()

print("HERHEHREHREHRE")
class TestInit(unittest.TestCase):
    def test_init(self):
        self.assertIsNotNone(IFACE, None)
        plugin = SMProcessing(IFACE)
        print(type(plugin.dlg))


if __name__ == "__main__":
    unittest.main()