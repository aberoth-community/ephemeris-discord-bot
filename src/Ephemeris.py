
import json
import numpy as np
import bisect

class Ephemeris:
    # add function to re calibrate and re calc cached events
    def __init__(self) -> None:
        self.glowThresh = 0.5
        self.darkThresh = 1
        self.variablesFile = "src\\variables.json"
        self.v = self.getVariables(self.variablesFile)
        self.periods = self.getPeriods()
        self.radii = self.getRadii()
        self.refTimes = self.getRefTimes()
        self.refOffsets = self.getRefOffsets()
        self.setRefPositions()
        self.refPositions = self.getRefPositions()
        
        # Boolean that indicates if orb is aligned
        # Ordered as ['shadow', 'white', 'black', 'green', 'red', 'purple', 'yellow', 'cyan', 'blue']
        self.alignmentStates = np.full(9, False)
        self.lastAlignmentStates = np.full(9, False)
        # self.lastAlignmentStates = [False, True, True, False, True, True, True, False, True]
        self.eventsCache = []
        self.setAlignmentStates(1713885673000)
        self.createAlignmentEvent(1713885673000)
        print(self.eventsCache)
        #print(self.calcAlignmentDifs(self.posRelCandle(1714005444000)))
    
    def createEventRange(self, startTime, stopTime, cache=False):
        pass
    
    def getEventsInRange(self, timeStart, timeEnd):
        # bisect O(log(n)), total O(2log(n))
        startIndex = bisect.bisect_left(self.eventsCache, (timeStart,))
        stopIndex = bisect.bisect_right(self.eventsCache, (timeEnd,))
        return [events for _, events in self.eventsCache[startIndex:stopIndex]]
    
    def createAlignmentEvent(self, timestamp):
        names = ['Shadow', 'White', 'Black', 'Green', 'Red', 'Purple', 'Yellow', 'Cyan', 'Blue']
        darkList = []
        glowList = []
        returnedToNormal = []
        aligned = []
        stillAligned = []
        for i, v in enumerate(self.alignmentStates):
            if v != self.lastAlignmentStates[i]:
                # if changed to being aligned
                if v == True:
                    aligned.append(names[i])
                # if changed to being unaligned
                else: returnedToNormal.append(names[i])
            # if still aligned
            elif v == True: stillAligned.append(names[i])
            
        if len(aligned) > 0 and (aligned[0] == names[0] or (len(stillAligned) > 0 and stillAligned[0] == names[0])): 
            darkList.extend(aligned)
            if len(stillAligned) > 0 and not self.lastAlignmentStates[0]: 
                darkList.extend(stillAligned)
        elif len(returnedToNormal) > 0 and returnedToNormal[0] == names[0]:
            if len(aligned) > 0: glowList.extend(aligned)
            if len(stillAligned) > 0: glowList.extend(stillAligned)
        else: glowList.extend(aligned)
            
        self.eventsCache.append((timestamp, {
            "newGlows": glowList,
            "newDarks": darkList,
            "returnedToNormal": returnedToNormal,
            # "discordTS": f'<t:{np.floor(timestamp/1000)}:D> <t:{np.floor(timestamp/1000)}:T>',
            # "discordRelTS": f'<t:{np.floor(timestamp/1000)}:R>'
        }))
    
    def setAlignmentStates(self, time):
        difs = self.calcAlignmentDifs(self.posRelCandle(time))
        for i, arr in enumerate(difs):
            if i == 0:
                alignmentPos = arr < self.darkThresh 
            else: 
                alignmentPos = arr < self.glowThresh
            for j in np.where(alignmentPos)[0]:
                self.alignmentStates[i] = self.alignmentStates[i+j+1] = True
        
        # for i, arr in enumerate(difs):
        #     for j, val in enumerate(arr):
        #         if (val < self.glowThresh or (i == 0 and val < self.darkThresh)):
        #             self.alignmentStates[i] = self.alignmentStates[i+j+1] = True            
        
    
    def calcAlignmentDifs(self, positions):
        return [abs((positions[i:9]%180) - (positions[i-1]%180)) for i in range(1,9)]
     
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