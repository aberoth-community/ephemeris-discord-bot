import json
import numpy as np


class VariableSolver:
    def __init__(self, moonPeriod: int = 1) -> None:
        # print('test')
        # long, short = self.calcAverageEventLength('packages\sampleData\glows\WhiteBlackSamples.json')
        # print('long Avg', long, 'short Avg', short)
        # print(self.formatTime(long), self.formatTime(short))
        # print(self.calcRadiusLong('src\sampleData\glows\WhiteYellowSamples.json', 1))
        print(self.calcRadiusShort("src\sampleData\glows\WhiteBlackSamples.json", 1))

    def calcAverageEventLength(self, fileExtention: str) -> tuple:

        longEvents = np.array([])
        shortEvents = np.array([])
        with open(fileExtention) as json_file:
            events = json.load(json_file)
        for set in events:
            if set == "Reference":
                continue
            for event in events[set]:
                CE = events[set][event]
                if CE["glowType"] == "long":
                    print((CE["endTime"] - CE["startTime"]))
                    longEvents = np.append(longEvents, CE["endTime"] - CE["startTime"])
                elif CE["glowType"] == "short":
                    shortEvents = np.append(
                        shortEvents, CE["endTime"] - CE["startTime"]
                    )
        print("long", longEvents, "short", shortEvents)
        return (np.average(longEvents), np.average(shortEvents))

    def calcRadiusLong(self, fileExtention: str, candleRadius: float = 1.0) -> float:
        """
        Calculates the radius from the white orb of an orb for which sample points are provided.
        Use for orbs that have a larger radius than the candle (not black or green).

        Parameters
        ---------
            fileExtention: `str`
                file extention for json file with the sample points for the orb.

            candleRadius: `float`
                The radius of the candle relative to the white orb. Default 1

        Returns
        ---------
            `float`
                The radius of the orb relative to the white orb. The radius is expressed as a ratio
                multiplied by the candle radius.
        """

        long, short = self.calcAverageEventLength(fileExtention)
        return candleRadius * ((short + long) / (long - short))

    def calcRadiusShort(self, fileExtention: str, candleRadius: float = 1.0) -> float:
        """
        Calculates the radius from the white orb of an orb for which sample points are provided.
        Use for orbs that have a smaller radius than the candle (black and green)

        Parameters
        ---------
            fileExtention: `str`
                file extention for json file with the sample points for the orb.

            candleRadius: `float`
                The radius of the candle relative to the white orb. Default 1

        Returns
        ---------
            `float`
                The radius of the orb relative to the white orb. The radius is expressed as a ratio
                multiplied by the candle radius.
        """

        long, short = self.calcAverageEventLength(fileExtention)
        return candleRadius * ((long - short) / (short + long))

    def calcAlignmentRange(self, dimStart: float, dimEnd: float) -> float:
        """Calculates the alignment range relative to the candle for an
        alignment event to happen.

        Parameters
        ---------
            dimStart: `float`
                The start time of a white dim event
            dimEnd: `float`
                The end time of the same dim event

        Returns
        ---------
            `float`
            A value representing the max angular distance between two bodies
            relative to the candle that still counts as aligned
        """
        pass

    def calcPeriodSlow(self) -> float:
        pass

    def calcPeriodFast(self) -> float:
        pass


VS = VariableSolver()
