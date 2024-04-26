
import json
import numpy as np

class Ephemeris:
    # add function to re calibrate and re calc cached events
    def __init__(self) -> None:
        self.variablesFile = "src\\variables.json"
        self.v = self.getVariables(self.variablesFile)
        self.periods = self.getPeriods()
        self.radii = self.getRadii()
        self.refTimes = self.getRefTimes()
        self.refOffsets = self.getRefOffsets()
        self.setRefPositions()
        self.refPositions = self.getRefPositions()
        
        print(self.posRelCandle(1714005444000))
    
    def checkAlignmentChange(self):
        # names = [shadow, white, black, green, etc]
        # outline of check set up
        # blkAlignments = [3:-1] - [2]
        # for range in blkAlignments
        #     if range < thresh and change state:
        #         add change state event
        # greenAlignments = [4:-1] - [3]
        # for range in greenAlignments
        #     if range < thresh and change state:
        #         add change state event
        pass
     
    def updatePositions(self): 
        pass
    
    def posRelCandle(self, time):
        rw = self.posRelWhite(time)
        positions = np.array([self.shadowPos(time), (rw[0]+180)%360])
        
        x = self.radii[1:8] * np.cos(np.radians(rw[1:8])) - np.cos(np.radians(rw[0]))
        y = self.radii[1:8] * np.sin(np.radians(rw[1:8])) - np.sin(np.radians(rw[0]))
        positions = np.append(positions, (np.degrees(np.arctan2(y, x))) % 360)
        return positions
    
    def posRelWhite(self, time):
        positions = ((360/self.periods)*(time-self.refTimes)+self.refPositions) % 360
        #positions[0] is white pos rel candle, add 180 to make it the candle pos rel white
        positions[0] = (positions[0]+180) % 360
        return positions
    
    def shadowPos(self, time):
        return ((360/self.v['shadow']['period'])*(time-self.v['shadow']['refTime'])+self.v['shadow']['refOffset']) % 360
    
    def setRefPositions(self):
        p = self.periods
        rt = self.refTimes
        ros = self.refOffsets
        shadow = self.v['shadow']
        
        self.v['candle']['refPos'] = ((360/shadow['period'])*(rt[0]-shadow['refTime'])+shadow['refOffset']) % 360
        
        posList = ((360/p[0])*(rt[1:8]-rt[0])+self.v['candle']['refPos']+ros[1:8]) % 360
        
        self.v['black']['refPos'] = posList[0]
        self.v['green']['refPos'] = posList[1]
        self.v['red']['refPos'] = posList[2]
        self.v['purple']['refPos'] = posList[3]
        self.v['yellow']['refPos'] = posList[4]
        self.v['cyan']['refPos'] = posList[5]
        self.v['blue']['refPos'] = posList[6]
        
        self.updateVariables(self.variablesFile)
    
    def getPeriods(self):
        return np.array([self.v['candle']['period'],
                        self.v['black']['period'],
                        self.v['green']['period'],
                        self.v['red']['period'],
                        self.v['purple']['period'],
                        self.v['yellow']['period'],
                        self.v['cyan']['period'],
                        self.v['blue']['period']])
    
    def getRadii(self):
        return np.array([self.v['candle']['radius'],
                        self.v['black']['radius'],
                        self.v['green']['radius'],
                        self.v['red']['radius'],
                        self.v['purple']['radius'],
                        self.v['yellow']['radius'],
                        self.v['cyan']['radius'],
                        self.v['blue']['radius']])
        
    def getRefTimes(self):
        return np.array([self.v['candle']['refTime'],
                        self.v['black']['refTime'],
                        self.v['green']['refTime'],
                        self.v['red']['refTime'],
                        self.v['purple']['refTime'],
                        self.v['yellow']['refTime'],
                        self.v['cyan']['refTime'],
                        self.v['blue']['refTime']])
    
    def getRefPositions(self):
        return np.array([self.v['candle']['refPos'],
                        self.v['black']['refPos'],
                        self.v['green']['refPos'],
                        self.v['red']['refPos'],
                        self.v['purple']['refPos'],
                        self.v['yellow']['refPos'],
                        self.v['cyan']['refPos'],
                        self.v['blue']['refPos']])
        
    def getRefOffsets(self):
        return np.array([self.v['candle']['refOffset'],
                        self.v['black']['refOffset'],
                        self.v['green']['refOffset'],
                        self.v['red']['refOffset'],
                        self.v['purple']['refOffset'],
                        self.v['yellow']['refOffset'],
                        self.v['cyan']['refOffset'],
                        self.v['blue']['refOffset']])
        
    def updateVariables(self, variablesFile):
        json_object = json.dumps(self.v, indent=4)
        with open(variablesFile, "w") as outfile:
            outfile.write(json_object)
    
    def getVariables(self, variablesFile):
        variables ={}
        with open(variablesFile, 'r') as json_file:
             variables = json.load(json_file)
        return variables
    
ephermis = Ephemeris()