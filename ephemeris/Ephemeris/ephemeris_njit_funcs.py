import numpy as np
from numba import njit


@njit
def posRelWhite(time: int, periods, refTimes, refPositions) -> np.ndarray[float]:
    """Calculates the position of each orb, excluding the shadow orb, relative to the
    white orb (sun equivalent)

    Parameters
    ---------
        time: `int`
            The epoch timestamp in ms at which the orb positions are retrieved.
    Returns
    ---------
    `np.ndarray[float]`
        An array with each index corresponding to the position of a unique orb or the candle in
        degrees relative to the white orb.
    """
    positions = ((360 / periods) * (time - refTimes) + refPositions) % 360
    # positions[0] is white pos rel candle, add 180 to make it the candle pos rel white
    positions[0] = (positions[0] + 180) % 360
    return positions
