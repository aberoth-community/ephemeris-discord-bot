import json
import numpy as np

class VariableSolver:
    def __init__(self, moonPeriod: int = 1) -> None:
        print('test')
        # long, short = self.calcAverageEventLength('packages\sampleData\glows\WhiteBlackSamples.json')
        # print('long Avg', long, 'short Avg', short)
        # print(self.format_time(long), self.format_time(short))
        print(self.calcRadiusShort('packages\sampleData\glows\WhiteBlackSamples.json', 149.6))
    
    def calcAverageEventLength(self, fileExtention: str) -> tuple:
        longEvents = np.array([])
        shortEvents = np.array([])
        with open(fileExtention) as json_file:
             events = json.load(json_file)
        for set in events:
            if set == 'Reference': 
                continue
            for event in events[set]:
                CE = events[set][event]
                if CE['glowType'] == 'long':
                    print((CE['endTime'] - CE['startTime']))
                    longEvents = np.append(longEvents, CE['endTime'] - CE['startTime'])
                elif CE['glowType'] == 'short':
                    shortEvents = np.append(shortEvents, CE['endTime'] - CE['startTime'])
        print('long', longEvents, 'short', shortEvents)
        return (np.average(longEvents), np.average(shortEvents))
                
    
    def calcRadiusLong(self, fileExtention: str, candleRadius: float = 1.0) -> float:
        """
        Calculates the radius from the white orb of an orb
        for which sample points are provided

        Args:
            fileExtention (str): file extention for json file with
            the sample points for the orb
            
            candleRadius (float = 1) Optional: the radius of the candle relative to the white orb
            the returned orb radius is ratio relative to this value

        Returns:
            float: a float representing the radius of the orb relative to the candle
        """
        
        long, short = self.calcAverageEventLength(fileExtention)
        return candleRadius*((short+long)/(long-short))
    
    def calcRadiusShort(self, fileExtention: str, candleRadius: float = 1.0) -> float:
        """
        Calculates the radius from the white orb of an orb
        for which sample points are provided

        Args:
            fileExtention (str): file extention for json file with
            the sample points for the orb
            
            candleRadius (float = 1) Optional: the radius of the candle relative to the white orb
            the returned orb radius is ratio relative to this value

        Returns:
            float: a float representing the radius of the orb relative to the candle
        """
        
        long, short = self.calcAverageEventLength(fileExtention)
        return candleRadius*((long-short)/(short+long))
    
    def calcAlignmentRange(self, dimStart: float, dimEnd: float) -> float:
        """Calculates the alignment range relative to the candle for an
        alignment event to happen.

        Args:
            dimStart (float): The start time of a white dim event
            dimEnd (float): The end time of the same dim event

        Returns:
            float: A value representing the max angular distance between two bodies
            relative to the candle that still counts as aligned
        """
        pass
    
    def calcPeriodSlow(self) -> float:
        pass
    
    def calcPeriodFast(self) -> float:
        pass
    
    def format_time(self, milliseconds):
        # Convert milliseconds to seconds
        seconds = milliseconds // 1000
        # Calculate hours, minutes and seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        # Return formatted time string
        return f"{hours:.0f}h {minutes:.0f}m {seconds:.0f}s"
    
VS = VariableSolver()