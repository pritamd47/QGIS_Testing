from qgis.core import (
    Qgis,
    QgsMessageLog
)
from numpy import array
import numpy as np
import numpy.ma as ma

def print_(*text, level=Qgis.Info):
    """Push messages to `messages` log as
       `Snow Melt runoff modelling Data Pre-Processing Log` through QGIS's
       message passing pipeline. Also updates the OutputPane
    
    Arguments:
        text {Any} -- What to print_/log. It will be passed through str(...)
            to change the arguments to string.

            Can also be multiple arguments - just like base print_ func
        """
    # TODO add feature: Calling this would send messages to both QgsMessage
    #  and outputPane (Logging pane in the dialog)

    # TODO Would be great if this print_ function could broadcast to
    #  various types of streams -- 1. QgsMessageLog  2. Print  3. OutputPane
    #  Look into the SMProcessingDialog.logMessage(...) function for #3.
    if len(text) > 1:
        text = ' '.join([str(arg) for arg in text])
        _print_to_message_board(text, level=level)
    else:
        text = str(text[0])
        _print_to_message_board(text, level=level)


def _print_to_message_board(text, level):
    """Sends the `text` to QgsMessageLog.

    Args:
        text: Message/text to send as string
        level: Qgis.Info/Qgis.Error/.. instance
    """
    message_board = "Snow Melt runoff modelling Data Pre-Processing Log"
    QgsMessageLog.logMessage(
        text,
        message_board,
        level=level
    )


def _print_to_output(text):
    """Sends the `text` to OutputPane (logging functionality in the plugin
    dialog)

    Args:
        text: Message/text to send as string
    """
    # TODO add code;
    pass


def rast_to_arr(layer): #Input: QgsRasterLayer
    """
    ref: https://gis.stackexchange.com/a/331099
    Args:
        layer {QgsRasterLayer}: QgsRasterLayer instance which will be converted
            to numpy array

    Returns:
        array(values) {numpy.array}: Array of values
    """
    values = []
    provider = layer.dataProvider()
    block = provider.block(1, layer.extent(), layer.width(), layer.height())
    for i in range(layer.width()):
        for j in range(layer.height()):
            values.append(block.value(i, j))
    return array(values)

def linear_regression(x, y):
    """Calculates the regression coefficients
    y=m*x+c

    c=$y$x^2 - $x$xy
     -------------
     n$x^2 - ($x)^2

    m=n$xy - $x$y
     --------------
     n$x^2 - ($x)^2

    Args:
        x{array or array like}: Independent variable.
                                Make sure no nans are present
        y{array or array like}: Dependent variable
                                Make sure no nans are present

    Returns:
        (c, m): Intercept and Slope of the fitted line
    """
    # Select the values where neither X nor Y is np.nan Drop nans
    # idx = np.where(~np.isnan(X + Y))

    # x = X[idx]
    # y = Y[idx]

    m_x, m_y = np.mean(x), np.mean(y)

    numerator = np.sum((x - m_x) * (y - m_y))
    denominator = np.sum((x - m_x) ** 2)

    m = numerator / denominator
    c = m_y - m*m_x

    return c, m
