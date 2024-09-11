import bisect
import json
import numpy as np
import time
from pathlib import Path

DEBUG = False

class Ephemeris:
    # add function to re calibrate and re calc cached events
    def __init__(self, start:int=0, end:int=0, numMoonCycles:int=5) -> None:
        self.glowThresh = 0.5
        self.darkThresh = 1
        self.increment = 60 * 1000
        self.oneAberothDay = 8640000
        self.noonRefTime = 1725903360554 # Night starts 42 minutes after
        self.variablesFile = Path("ephemeris/Ephemeris/variables.json")
        self.cacheFile = Path("ephemeris/Ephemeris/cache.json")
        self.newRefTimeFile = Path("ephemeris/UpdateWebServer/newRefTimes.json")
        self.v:dict[str, dict] = self.getVariables(self.variablesFile)
        self.periods = self.getPeriods()
        self.radii = self.getRadii()
        self.refTimes = self.getRefTimes()
        self.refOffsets = self.getRefOffsets()
        self.setRefPositions()
        self.refPositions = self.getRefPositions()

        # Boolean that indicates if orb is aligned with another orb or the shadow orb
        # Ordered as ['shadow', 'white', 'black', 'green', 'red', 'purple', 'yellow', 'cyan', 'blue']
        self.alignmentStates = np.full(9, False)
        self.lastAlignmentStates = np.full(9, False)
        self.scrollEventsCache = []
        self.scrollEventsCache = self.createScrollEventRange(start, end)
        self.moonCyclesCache = self.createLunarCalendar(start, numMoonCycles)
        self.saveCache(self.cacheFile)

    def createScrollEventRange(self, startTime:int, stopTime:int, saveToCache:bool=False) -> list[tuple[int, dict[str, any]]]:
        currentTime = startTime
        tempCache = []
        # create event for the starting alignments
        self.lastAlignmentStates = np.full(9, False)
        self.setAlignmentStates(currentTime)
        tempCache.append(self.createAlignmentEvent(currentTime))
        # colon is IMPORTANT, creates shallow copy of list instead of copy by ref
        self.lastAlignmentStates = self.alignmentStates[:]
        # iterate through time range and find events
        while currentTime < stopTime:
            self.setAlignmentStates(currentTime)
            if self.checkForAlignmentChange():
                currentTime -= self.increment
                # if an alignment is found go back a step and step through with small step size to find more accurate start
                while currentTime <= (currentTime + self.increment):
                    self.setAlignmentStates(currentTime)
                    if self.checkForAlignmentChange():
                        tempCache.append(self.createAlignmentEvent(currentTime))
                        # colon is IMPORTANT, creates shallow copy of list instead of copy by ref
                        self.lastAlignmentStates = self.alignmentStates[:]
                        break
                    currentTime += 1000
            currentTime += self.increment
        if saveToCache:
            self.scrollEventsCache = tempCache
            self.saveCache(self.cacheFile)
        return tempCache

    def getScrollEventsInRange(self, startTime:int, endTime:int) -> list:
        # bisect O(log(n)), total O(2log(n))
        startIndex = bisect.bisect_left(self.scrollEventsCache, (startTime,))
        stopIndex = bisect.bisect_right(self.scrollEventsCache, (endTime,))
        return [events for _, events in self.scrollEventsCache[startIndex:stopIndex]]

    def checkForAlignmentChange(self) -> bool:
        return not np.array_equal(self.alignmentStates, self.lastAlignmentStates)

    def createAlignmentEvent(self, timestamp:int) -> tuple[int, dict[str, any]]:
        names = [
            "Shadow",
            "White",
            "Black",
            "Green",
            "Red",
            "Purple",
            "Yellow",
            "Cyan",
            "Blue",
        ]
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
                else:
                    returnedToNormal.append(names[i])
            # if still aligned
            elif v == True:
                stillAligned.append(names[i])

        # if anything is aligns with the shadow orb or aligns while something else is already aligned with the shadow orb  
        if len(aligned) > 0 and (
            aligned[0] == names[0]
            or (len(stillAligned) > 0 and stillAligned[0] == names[0])
        ):
            # add all the newly aligned orbs to the new dark list
            darkList.extend(aligned)
            # if there are orbs previously aligned
            if len(stillAligned) > 0 and not self.lastAlignmentStates[0]:
                # add the previously aligned orbs to the dark list if there is a new dark
                darkList.extend(stillAligned)
        # if alignments with the shadow orb end
        elif len(returnedToNormal) > 0 and returnedToNormal[0] == names[0]:
            if len(aligned) > 0:
                # add newly aligned orbs to glow list
                glowList.extend(aligned)
            # if there are orbs that are still aligned (were previously glowing)
            if len(stillAligned) > 0:
                # add the still aligned orbs to the glow list
                glowList.extend(stillAligned)
        else:
            # if not a new dark or returning to normal, newly algined orbs should be glowing
            glowList.extend(aligned)
        
        if (DEBUG):
            difs = self.calcAlignmentDifs(self.posRelCandle(timestamp))
            eventStr = '\n'.join(f"{difs[0][i] }, {names[i+1]}" for i in range(0, 8))
            print(eventStr)
            print((
                timestamp,
                {
                    "newGlows": glowList,
                    "newDarks": darkList,
                    "returnedToNormal": returnedToNormal,
                    "discordTS": f"<t:{int(np.floor(timestamp/1000))}:D> <t:{int(np.floor(timestamp/1000))}:T>",
                    # "discordRelTS": f'<t:{np.floor(timestamp/1000)}:R>'
                },
            ))
        
        return (
            timestamp,
            {
                "newGlows": glowList,
                "newDarks": darkList,
                "returnedToNormal": returnedToNormal,
                "discordTS": f"<t:{int(np.floor(timestamp/1000))}:D> <t:{int(np.floor(timestamp/1000))}:T>",
                # "discordRelTS": f'<t:{np.floor(timestamp/1000)}:R>'
            },
        )

    def setAlignmentStates(self, time:int) -> None:
        self.alignmentStates = np.full(9, False)
        difs = self.calcAlignmentDifs(self.posRelCandle(time))
        for i, arr in enumerate(difs):
            if i == 0:
                alignmentPos = arr < self.darkThresh
            else:
                alignmentPos = arr < self.glowThresh
            for j in np.where(alignmentPos)[0]:
                self.alignmentStates[i] = self.alignmentStates[i + j + 1] = True

    def calcAlignmentDifs(self, positions:np.ndarray[float]) -> list:
        difs = []
        # for each orb
        for i in range(1, 9):
            # calculate the difference between that orb and other orbs that haven't been compared yet
            tempArr = abs((positions[i:9] % 180) - (positions[i - 1] % 180))
            # if the dif is greater than 90, set the value to 180 minus value to check for opposite alignments
            tempArr[tempArr > 90] = 180 - tempArr[tempArr > 90]
            # add the alignment comparisons for the current orb to the dif list
            difs.append(tempArr)
        return difs

    def posRelCandle(self, time:int) -> np.ndarray[float]:
        rw = self.posRelWhite(time)
        positions = np.array([self.getShadowPos(time), (rw[0] + 180) % 360])

        x = self.radii[1:8] * np.cos(np.radians(rw[1:8])) - np.cos(np.radians(rw[0]))
        y = self.radii[1:8] * np.sin(np.radians(rw[1:8])) - np.sin(np.radians(rw[0]))
        positions = np.append(positions, (np.degrees(np.arctan2(y, x))) % 360)
        return positions

    def posRelWhite(self, time:int) -> np.ndarray[float]:
        positions = (
            (360 / self.periods) * (time - self.refTimes) + self.refPositions
        ) % 360
        # positions[0] is white pos rel candle, add 180 to make it the candle pos rel white
        positions[0] = (positions[0] + 180) % 360
        return positions

    def getShadowPos(self, time:int) -> float:
        return (
            (360 / self.v["shadow"]["period"]) * (time - self.v["shadow"]["refTime"])
            + self.v["shadow"]["refOffset"]
        ) % 360

    def setRefPositions(self) -> None:
        p = self.periods
        rt = self.refTimes
        ros = self.refOffsets
        shadow = self.v["shadow"]

        self.v["candle"]["refPos"] = (
            (360 / shadow["period"]) * (rt[0] - shadow["refTime"]) + shadow["refOffset"]
        ) % 360

        posList = (
            (360 / p[0]) * (rt[1:8] - rt[0]) + self.v["candle"]["refPos"] + ros[1:8]
        ) % 360

        self.v["black"]["refPos"] = posList[0]
        self.v["green"]["refPos"] = posList[1]
        self.v["red"]["refPos"] = posList[2]
        self.v["purple"]["refPos"] = posList[3]
        self.v["yellow"]["refPos"] = posList[4]
        self.v["cyan"]["refPos"] = posList[5]
        self.v["blue"]["refPos"] = posList[6]

        self.updateVariables()

    def getPeriods(self) -> np.ndarray[int]:
        return np.array(
            [
                self.v["candle"]["period"],
                self.v["black"]["period"],
                self.v["green"]["period"],
                self.v["red"]["period"],
                self.v["purple"]["period"],
                self.v["yellow"]["period"],
                self.v["cyan"]["period"],
                self.v["blue"]["period"],
            ]
        )

    def getRadii(self) -> np.ndarray[float]:
        return np.array(
            [
                self.v["candle"]["radius"],
                self.v["black"]["radius"],
                self.v["green"]["radius"],
                self.v["red"]["radius"],
                self.v["purple"]["radius"],
                self.v["yellow"]["radius"],
                self.v["cyan"]["radius"],
                self.v["blue"]["radius"],
            ]
        )

    def getRefTimes(self) -> np.ndarray[int]:
        return np.array(
            [
                self.v["candle"]["refTime"],
                self.v["black"]["refTime"],
                self.v["green"]["refTime"],
                self.v["red"]["refTime"],
                self.v["purple"]["refTime"],
                self.v["yellow"]["refTime"],
                self.v["cyan"]["refTime"],
                self.v["blue"]["refTime"],
            ]
        )

    def getRefPositions(self) -> np.ndarray[float]:
        return np.array(
            [
                self.v["candle"]["refPos"],
                self.v["black"]["refPos"],
                self.v["green"]["refPos"],
                self.v["red"]["refPos"],
                self.v["purple"]["refPos"],
                self.v["yellow"]["refPos"],
                self.v["cyan"]["refPos"],
                self.v["blue"]["refPos"],
            ]
        )

    def getRefOffsets(self) -> np.ndarray[int]:
        return np.array(
            [
                self.v["candle"]["refOffset"],
                self.v["black"]["refOffset"],
                self.v["green"]["refOffset"],
                self.v["red"]["refOffset"],
                self.v["purple"]["refOffset"],
                self.v["yellow"]["refOffset"],
                self.v["cyan"]["refOffset"],
                self.v["blue"]["refOffset"],
            ]
        )

    def saveCache(self, fileLoc:Path) -> None:
        json_object = json.dumps(self.scrollEventsCache, indent=4)
        with open(fileLoc, "w") as outfile:
            outfile.write(json_object)
        # print(f"[{time.time():.0f}] Saved Event Range to Cache File")

    def updateVariables(self) -> None:
        json_object = json.dumps(self.v, indent=4)
        with self.variablesFile.open("w") as outfile:
            outfile.write(json_object)

    def getVariables(self, variablesFile:Path) -> dict[str, dict]:
        variables = {}
        with variablesFile.open("r") as json_file:
            variables = json.load(json_file)
        return variables

    def autoRefreshCache(self, refreshRate:int=60 * 60 * 12):
        """Updates variables with any more recent and reference times received then automatically regenerates the cache. 
        Should Be used with an asnychronous wrapper.
    
        Args:
            refreshRate (int): The frequency in seconds to refresh the cache
        """
        while True:
            #time.sleep(refreshRate)
            self.updateRefTimes()
            self.createScrollEventRange(
                startTime=(time.time() * 1000) - 2 * 86400000,
                stopTime=(time.time() * 1000) + 12 * 86400000,
                saveToCache=True
            )
            print("New Cache Last Item:", self.scrollEventsCache[-1])
            time.sleep(60*3)
            
    def updateScrollCache(self, start:int, stop:int) -> None:
        self.updateRefTimes()
        self.createScrollEventRange(
            startTime=start,
            stopTime=stop,
            saveToCache=True
        )
        # print("New Cache Last Item:", self.eventsCache[-1])

    def updateMoonCache(self, start:int, numMoonCycles:int) -> None:
        self.updateRefTimes()
        self.createLunarCalendar(start, numMoonCycles)

    def updateRefTimes(self) -> None:
        newVars:dict[str, list[int]] = {}
        with self.newRefTimeFile.open("r") as f:
            newVars = json.load(f)
        
        for orb in newVars:
            compOrb = orb if orb != 'white' else 'candle'
            # Check if current ref time is most recent refTime and check that it's within an expected alignment time range
            if (self.v[compOrb]['refTime'] != (newVars[orb][0]+newVars[orb][1]-500)/2) and self.checkValidRefTime(orb, newVars[orb]):
                # average two times then subtract the total average time the events are off by
                eventTime = round((newVars[orb][0]+newVars[orb][1]-500)/2)
                posistions = self.posRelWhite(eventTime)
                if orb == 'white': orb = 'candle'
                indicies = {"candle": 0, "black": 1, "green": 2, "red": 3, "purple": 4, "yellow": 5, "cyan": 6, "blue": 7}
                orbPos = posistions[indicies[orb]]
                candlePos = posistions[indicies["candle"]]
                # check if orb and candle are on same or opposite sides
                refOffset = min([0, 180, 360], key=lambda x: abs(x - (orbPos - candlePos)))
                if refOffset == 360: refOffset = 0
                # update variables
                self.v[orb]['refTime'] = eventTime
                self.v[orb]['refOffset'] = refOffset
        # reset arrays used to calculate events
        self.periods = self.getPeriods()
        self.radii = self.getRadii()
        self.refTimes = self.getRefTimes()
        self.refOffsets = self.getRefOffsets()
        self.setRefPositions()
        self.refPositions = self.getRefPositions()
        # Update the variables file to match the new refTimes
        self.updateVariables()
        
    def checkValidRefTime(self, orb:str, refTimes:list[int]) -> bool:
        startRange = self.getScrollEventsInRange(startTime=refTimes[0]-15000, endTime=refTimes[0]+15000)
        endRange = self.getScrollEventsInRange(startTime=refTimes[1]-15000, endTime=refTimes[1]+15000)
        if len(startRange) == 0 or len(endRange) == 0:
            return False
        orb = orb.capitalize()
        # white orb position is determined from darks rather than glows
        validStart = False
        validEnd = False
        if orb == 'White':
            for event in startRange:
                if orb in event["newDarks"]:
                    validStart = True
        else:
            for event in startRange:
                if orb in event["newGlows"]:
                    validStart = True
        if validStart == True:
            for event in endRange:
                if orb in event["returnedToNormal"]:
                    validEnd = True
        # print("Orb:", orb, (validStart and validEnd))
        return (validStart and validEnd)
        
    def createLunarCalendar(self, startTime:int, numMoonCycles:int) -> list[tuple[int, dict[str, any]]]: 
        """_summary_

        Args:
            startTime (int): The epoch time in ms for which events after will recorded
            numMoonCycles (int): The number of events for each phase that will be recorded

        Returns:
            list[tuple[int, dict[str, any]]]: A list of tuples containing the epoch time at which the moon change happens and\n
            a dictionary containing the name of the new phase and a discord timestamp for the event.
        """
        # 8 phases in one moon cycle plus almost full and almost new
        numEvents = numMoonCycles * 10
        currentTime = self.getLastNoonTime(startTime)
        tempCache = []
        
        dayStartWPos = self.getWhitePos(currentTime)
        dayStartSPos = self.getShadowPos(currentTime)
        while len(tempCache) < numEvents:
            phase = ''
            nextPhase = ''
            nextNoonTime = currentTime + self.oneAberothDay
            dayEndWPos = self.getWhitePos(nextNoonTime)
            dayEndSPos = self.getShadowPos(nextNoonTime)
            
            lunarCycleStartPos = (dayStartSPos - dayStartWPos + 360) % 360
            lunarCycleEndPos = (dayEndSPos - dayEndWPos + 360) % 360
            
            if lunarCycleStartPos < 360 and lunarCycleStartPos > 347.5 and (lunarCycleEndPos > 360 or lunarCycleEndPos < 12.5):
                phase = "new"
                nextPhase = "waxing_crescent"
            elif lunarCycleStartPos < 90 and lunarCycleEndPos > 90:
                phase = "first_quarter"
                nextPhase = "waxing_gibbous"
            elif lunarCycleStartPos < 180 and lunarCycleEndPos > 180:
                phase = "full"
                nextPhase = "waning_gibbous"
            elif lunarCycleStartPos < 270 and lunarCycleEndPos > 270:
                phase = "third_quarter"
                nextPhase = "waning_crescent"
              
            if phase != '':
                tempCache.append((
                    currentTime,
                    {
                        "phase": phase,
                        "discordTS": f"<t:{int(np.floor(currentTime/1000))}:D> <t:{int(np.floor(currentTime/1000))}:T>"
                        # "discordRelTS": f'<t:{np.floor(currentTime/1000)}:R>'
                    }
                ))
                print(tempCache[-1], lunarCycleStartPos, lunarCycleEndPos)
                tempCache.append((
                    nextNoonTime,
                    {
                        "phase": nextPhase,
                        "discordTS": f"<t:{int(np.floor(nextNoonTime/1000))}:D> <t:{int(np.floor(nextNoonTime/1000))}:T>"
                        # "discordRelTS": f'<t:{np.floor(nextNoonTime/1000)}:R>'
                    }
                ))
                print(tempCache[-1])
                # every phase except the exclictly checked ones last 5 to 6 days
                currentTime = currentTime + 5 * self.oneAberothDay
                
                dayStartWPos = self.getWhitePos(currentTime)
                dayStartSPos = self.getShadowPos(currentTime)
            else:
                dayStartWPos = dayEndWPos
                dayStartSPos = dayEndSPos
                currentTime = nextNoonTime
        # print(tempCache)
        firstPhase = tempCache[0][1]["phase"]
        previousPhase = ''
        if firstPhase == "new": previousPhase = "waning_crescent"
        elif firstPhase == "first_quarter": previousPhase = "waxing_crescent"
        elif firstPhase == "full": previousPhase = "waxing_gibbous"
        elif firstPhase == "third_quarter": previousPhase = "waning_gibbous"
        
        # tempCache.insert(0, previousPhase)
        #print(tempCache)
        return tempCache
        
    def getLastNoonTime(self, time:int) -> int:
        """
        Args:
            time (int): The epoch time in ms for which the previous Aberoth noon will be found.

        Returns:
            int: The epoch time in ms of the last Aberoth noon before the passed in time.
        """
        return time - ((time - self.noonRefTime) % self.oneAberothDay)
        
    def getWhitePos(self, time:int) -> float:
        position = (
        (360 / self.periods[0]) * (time - self.refTimes[0]) + self.refPositions[0]) % 360
        # positions[0] is white pos rel candle
        return position
    
if __name__ == "__main__":
    ephermis = Ephemeris(
        start=round((time.time() * 1000) - 10 * 86400000),
        end=round((time.time() * 1000) + 16 * 86400000),
    )
