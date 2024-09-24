import bisect
import json
import numpy as np
import time
from pathlib import Path
from os import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed

DEBUG = False


class Ephemeris:
    def __init__(
        self,
        start: int = 0,
        end: int = 0,
        numMoonCycles: int = 0,
        discordTimestamps: bool = False,
        multiProcess: bool = True,
        numCores: int | None = None,
    ) -> None:
        self.multiProcess = multiProcess
        self.numCores = numCores
        if multiProcess:
            cpuCount = cpu_count() or 1
            if numCores:
                if numCores > cpuCount:
                    print(
                        "numCores greater than number of available CPU cores, defaulting to 1"
                    )
                    self.numCores = 1
            else:
                self.numCores = cpuCount

        self.glowThresh = 0.5
        self.darkThresh = 1
        self.increment = 60 * 1000
        self.oneAberothDay = 8640000
        self.noonRefTime = 1725903360554  # Night starts 42 minutes after
        self.variablesFile = Path("ephemeris/Ephemeris/variables.json")
        self.cacheFile = Path("ephemeris/Ephemeris/cache.json")
        self.newRefTimeFile = Path("ephemeris/UpdateWebServer/newRefTimes.json")
        self.v: dict[str, dict] = self.getVariables(self.variablesFile)
        self.periods = self.getPeriods()
        self.radii = self.getRadii()
        self.refTimes = self.getRefTimes()
        self.refOffsets = self.getRefOffsets()
        self.setRefPositions()
        self.refPositions = self.getRefPositions()

        # Boolean that indicates if orb is aligned with another orb or the shadow orb
        # Ordered as ['shadow', 'white', 'black', 'green', 'red', 'purple', 'yellow', 'cyan', 'blue']
        self.currentAlignmentStates = np.full(9, False)
        self.lastAlignmentStates = np.full(9, False)
        self.scrollEventsCache = []
        self.scrollEventsCache = self.multiProcessCreateScrollEventRange(start, end)
        self.moonCyclesCache = self.createLunarCalendar(start, numMoonCycles)
        self.saveCache(self.cacheFile)

    def createScrollEventRange(
        self, startTime: int, stopTime: int, saveToCache: bool = False
    ) -> list[tuple[int, dict[str, any]]]:
        """Creates a chronologically ordered `list` of `tuples` that each
        contain information on a unique change in scroll/alignment states

        Parameters
        ------------
        startTime: `int`
            The epoch time in ms that alignment calculations will start from.
        stopTime: `int`
            The epoch time in ms that alignment calculations will stop at.
        saveToCache: `bool` *(optional)*
            When set to true the cache contents will be outputed
            to a local file. Defaults to False.

        Returns
        ---------
        `list[tuple[int, dict[str, any]]]`
            A chronologically ordered `list` of `tuples` that contain a timestamp and a dictionary containing
            information about the changed phases and a discord timestamp for the event.
        """
        if startTime == stopTime or startTime > stopTime:
            print("stopTime must be greater than startTime")
            return []

        currentTime = startTime
        tempCache = []
        # create event for the starting alignments
        self.lastAlignmentStates = np.full(9, False)
        self.currentAlignmentStates = self.setAlignmentStates(currentTime)
        # tempCache.append(self.createAlignmentEvent(currentTime))

        # colon is IMPORTANT, creates shallow copy of list instead of copy by ref
        self.lastAlignmentStates = self.currentAlignmentStates[:]
        # iterate through time range and find events
        while currentTime < stopTime:
            self.currentAlignmentStates = self.setAlignmentStates(currentTime)
            if self.checkForAlignmentChange():
                currentTime -= self.increment
                # if an alignment is found go back a step and step through with small step size to find more accurate start
                while currentTime <= (currentTime + self.increment):
                    self.currentAlignmentStates = self.setAlignmentStates(currentTime)
                    if self.checkForAlignmentChange():
                        tempCache.append(self.createAlignmentEvent(currentTime))
                        # colon is IMPORTANT, creates shallow copy of list instead of copy by ref
                        self.lastAlignmentStates = self.currentAlignmentStates[:]
                        break
                    currentTime += 1000
            currentTime += self.increment
        if saveToCache:
            self.scrollEventsCache = tempCache
            self.saveCache(self.cacheFile)
        return tempCache

    def multiProcessCreateScrollEventRange(
        self, startTime: int, stopTime: int, saveToCache: bool = False
    ) -> list[tuple[int, dict[str, any]]]:
        """Splits the time range into chunks and utilizes multi-processing inorder to make a chronologically
        ordered `list` of `tuples` that each contain information on a unique change in scroll/alignment states

        Parameters
        ------------
        startTime: `int`
            The epoch time in ms that alignment calculations will start from.
        stopTime: `int`
            The epoch time in ms that alignment calculations will stop at.
        saveToCache: `bool` *(optional)*
            When set to true the cache contents will be outputed
            to a local file. Defaults to False.

        Returns
        ---------
        `list[tuple[int, dict[str, any]]]`
            A chronologically ordered `list` of `tuples` that contain a timestamp and a dictionary containing
            information about the changed phases and a discord timestamp for the event.
        """
        if not self.multiProcess or self.numCores == 1:
            # use normal process when only one core is available
            return self.createScrollEventRange(startTime, stopTime, saveToCache)
        if startTime == stopTime or startTime > stopTime:
            # if the time range is not valid return
            print("stopTime must be greater than startTime")
            return []
        # convert float to int
        startTime = int(startTime)
        stopTime = int(stopTime)

        # divid the time range into ~equal chunks for each core
        chunkSize = (stopTime - startTime) // self.numCores
        chunks = []
        chunkNum = 0
        for chunkStart in range(startTime, stopTime, chunkSize):
            # package chunk information to be passed as an argument
            chunks.append(
                (
                    chunkStart,
                    (
                        chunkEnd
                        if (chunkEnd := chunkStart + chunkSize) <= stopTime
                        else stopTime
                    ),
                    chunkNum,
                )
            )
            chunkNum += 1

        retries = 0
        max_retries = 3
        while retries < max_retries:
            # try creating event cache with multi-processing
            try:
                tempCache = self.createProcessPool(chunks)
                print("Cache Created!")
                break
            except Exception as e:
                # retry up to three times before abandoning the calculation
                print(f"Error during processing: {e}")
                retries += 1
                if retries >= max_retries:
                    print(f"Failed after {max_retries} retries: {e}")
                    raise
                else:
                    print(f"Retrying... ({retries}/{max_retries})")

        if saveToCache:
            self.scrollEventsCache = tempCache
            self.saveCache(self.cacheFile)
        return tempCache

    def createProcessPool(
        self, chunks: tuple[int, int, int]
    ) -> list[tuple[int, dict[str, any]]]:
        """Creates a proccess pool and assigns the time chunks evenly to each process. Each process process makes
        its own chronologically ordered `list` of `tuples` that each contain information on a unique change in scroll/alignment states.
        before they're recombined into a bigger cache that spans the whole time range.

        Parameters
        ------------
        chunks: `tuple[int, int, int]`
            A tuple containing the start and stop time of each chunk as an epoch timestamp in ms as well as
            an integer that indicates where in the final cache the results should be inserted.

        Returns
        ---------
        `list[tuple[int, dict[str, any]]]`
            A chronologically ordered `list` of `tuples` that contain a timestamp and a dictionary containing
            information about the changed phases and a discord timestamp for the event.
        """
        with ProcessPoolExecutor(max_workers=self.numCores) as executor:
            futures = {
                executor.submit(
                    self.processScrollTimeRange, chunkStart, chunkEnd, chunkNum
                ): chunkNum
                for chunkStart, chunkEnd, chunkNum in chunks
            }
            # Note: this section sorts data similar to a priority queue but allows inserting the
            # whole chunk at once rather than the elements individually
            tempCache = [None] * len(chunks)
            for future in as_completed(futures):
                chunkNum = futures[future]
                try:
                    chunkCache = future.result()
                    tempCache[chunkNum] = chunkCache
                except Exception as e:
                    print(f"Exception in chunk {chunkNum}: {e}")
                    # re-raise to propagate the exception
                    raise
            # reverse traverse
            for i in range(len(chunks) - 1, -1, -1):
                # unpack the lists of events stored in each index in tempCache
                tempCache[i : i + 1] = tempCache[i]
        return tempCache

    def processScrollTimeRange(
        self, startTime, stopTime, chunkNum=None
    ) -> list[tuple[int, dict[str, any]]]:
        """Creates a chronologically ordered `list` of `tuples` that each contain information on a unique change in scroll/alignment states.
        Multi-processing friendly

        Parameters
        ------------
        startTime: `tuple[int, int, int]`
            An epoch timestamp in ms that represents the time at which calculations will start at.
        stopTime: `tuple[int, int, int]`
            An epoch timestamp in ms that represents the time at which calculations will stop at.
        chunkNum: `int`
            An integer that indicates where in the final cache the results should be inserted.

        Returns
        ---------
        `list[tuple[int, dict[str, any]]]`
            A chronologically ordered `list` of `tuples` that contain a timestamp and a dictionary containing
            information about the changed phases and a discord timestamp for the event.
        """
        try:
            currentTime = startTime
            tempCache = []
            # Set starting state
            lastAlignmentStates = np.full(9, False)
            currentAlignmentStates = self.setAlignmentStates(currentTime)

            # colon is IMPORTANT, creates shallow copy of list instead of copy by ref
            lastAlignmentStates = currentAlignmentStates[:]
            # iterate through time range and find events
            while currentTime < stopTime:
                currentAlignmentStates = self.setAlignmentStates(currentTime)
                if self.checkForAlignmentChange(
                    lastAlignmentStates, currentAlignmentStates
                ):
                    currentTime -= self.increment
                    # if an alignment is found go back a step and step through with small step size to find more accurate start
                    while currentTime <= (currentTime + self.increment):
                        currentAlignmentStates = self.setAlignmentStates(currentTime)
                        if self.checkForAlignmentChange(
                            lastAlignmentStates, currentAlignmentStates
                        ):
                            tempCache.append(
                                self.createAlignmentEvent(
                                    currentTime,
                                    lastAlignmentStates,
                                    currentAlignmentStates,
                                )
                            )
                            # colon is IMPORTANT, creates shallow copy of list instead of copy by ref
                            lastAlignmentStates = currentAlignmentStates[:]
                            break
                        currentTime += 1000
                currentTime += self.increment
        except Exception as e:
            print(f"Exception in worker process for chunk {chunkNum}: {e}")
            raise  # re-raise to propagate the exception
        return tempCache

    def getScrollEventsInRange(
        self, startTime: int, endTime: int
    ) -> list[tuple[int, dict[str, any]]]:
        """Subsections self.scrollEventsCache in O(2log(n)) time to only include all
        predicted events between the start and stop time. Does not change order of events.

        Parameters
        ------------
        startTime: `int`
            The epoch time in ms that alignment calculations will start from.
        stopTime: `int`
            The epoch time in ms that alignment calculations will stop at.

        Returns
        ---------
        `list[tuple[int, dict[str, any]]]`
            A chronologically ordered `list` of `tuples` that contains the predicted events' information.
        """
        # bisect O(log(n)), total O(2log(n))
        startIndex = bisect.bisect_left(self.scrollEventsCache, (startTime,))
        stopIndex = bisect.bisect_right(self.scrollEventsCache, (endTime,))
        return [events for _, events in self.scrollEventsCache[startIndex:stopIndex]]

    def checkForAlignmentChange(
        self, lastAlignmentStates=[], currentAlignmentStates=[]
    ) -> bool:
        """Checks to see if there has been a change in alignments between the states
        at the current time and previously calculated time

        Returns
        ---------
        `bool`
            True if any alignment state has changed from the previous alignment check.
        """
        #
        if len(lastAlignmentStates) < 1:
            lastAlignmentStates = self.lastAlignmentStates
        if len(currentAlignmentStates) < 1:
            currentAlignmentStates = self.currentAlignmentStates
        return not np.array_equal(currentAlignmentStates, lastAlignmentStates)

    def createAlignmentEvent(
        self, timestamp: int, lastAlignmentStates=[], currentAlignmentStates=[]
    ) -> tuple[int, dict[str, any]]:
        """Creates a `tuple` containing the epoch timestamp in ms at which the alignment
        changes and a `dict` containing information about the event.

        Parameters
        ---------
        timestamp: `int`
            The epoch time in ms that alignment change happens

        Returns
        ---------
        `tuple[int, dict[str, any]]`
            A `tuple` who's first element is the epoch time stamp in ms for the event
            and the second element is a `dict` containing the event information.

        """
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
        if len(lastAlignmentStates) < 1:
            lastAlignmentStates = self.lastAlignmentStates
        if len(currentAlignmentStates) < 1:
            currentAlignmentStates = self.currentAlignmentStates
        for i, v in enumerate(currentAlignmentStates):
            if v != lastAlignmentStates[i]:
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
            if len(stillAligned) > 0 and not lastAlignmentStates[0]:
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

        # does not run in prod
        if DEBUG:
            difs = self.calcAlignmentDifs(self.posRelCandle(timestamp))
            eventStr = "\n".join(f"{difs[0][i] }, {names[i+1]}" for i in range(0, 8))
            print(eventStr)
            print(
                (
                    timestamp,
                    {
                        "newGlows": glowList,
                        "newDarks": darkList,
                        "returnedToNormal": returnedToNormal,
                        "discordTS": f"<t:{int(np.floor(timestamp/1000))}:D> <t:{int(np.floor(timestamp/1000))}:T>",
                        # "discordRelTS": f'<t:{np.floor(timestamp/1000)}:R>'
                    },
                )
            )

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

    # UPDATE DOCK STRING, RETURNS NOW
    def setAlignmentStates(self, time: int) -> None:
        """Gets the difference in position between all orbs and determines if each orb is in an
        aligned state using that information. Stores this information as a boolean in the list
        self.alignmentStates[i] with True corresponding to being aligned with any other orb.

        Parameters
        ---------
            time: `int`
                The epoch timestamp in ms at which orb positions are retrieved.
        """
        alignmentStates = np.full(9, False)
        # get the differences at the given time
        difs = self.calcAlignmentDifs(self.posRelCandle(time))
        for i, arr in enumerate(difs):
            # the first index corresponds to the list of differences between
            # the shadow orb other orbs sorted by their proximity to the white orb
            if i == 0:
                # checks if any of the orbs are with in the larger
                # threshold for alignment with the shadow orb
                alignmentPos = arr < self.darkThresh
            else:
                # all other orbs have the same threshhold of alignment
                alignmentPos = arr < self.glowThresh
            for j in np.where(alignmentPos)[0]:
                # gets the indices of the orbs that are aligned with the current orb
                # sets the current orb and that indice to True (aligned) in the alignments states list
                alignmentStates[i] = alignmentStates[i + j + 1] = True
        return alignmentStates

    def calcAlignmentDifs(
        self, positions: np.ndarray[float]
    ) -> list[np.ndarray[float]]:
        """Calculates the difference between the positions of each orb relative to the candle (earth equivalent).

        Parameters
        ---------
            positions: `np.ndarray[float]`
                a list of the angular positions in degrees of each orb relative to the candle.
        Returns
        ---------
        `list[np.ndarray[float]]`
            Each `np.ndarray` within the `list` corresponds to an orb with the elements of the
            array being the difference in angular position between the orb and all other orbs that
            have not been compared to the orb for which the array belongs to.
        """
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

    def posRelCandle(self, time: int) -> np.ndarray[float]:
        """Gets the position of each orb relative to the candle (earth equivalent)

        Parameters
        ---------
            time: `int`
                The epoch timestamp in ms at which the orb positions are retrieved.
        Returns
        ---------
        `np.ndarray[float]`
            An array with each index corresponding to the position of a unique orb relative to the candle.
        """
        # get the positions of the orbs relative to white, exluding the shadow orb
        rw = self.posRelWhite(time)
        # prepend the shadow orb (moon equivalent) position relative to the candle
        positions = np.array([self.getShadowPos(time), (rw[0] + 180) % 360])

        # find the x and y offset of the of the orbs relative to the candle
        # note candle implicity has a radius of 1, or 1 AU and planet raddi are in AU
        x = self.radii[1:8] * np.cos(np.radians(rw[1:8])) - np.cos(np.radians(rw[0]))
        y = self.radii[1:8] * np.sin(np.radians(rw[1:8])) - np.sin(np.radians(rw[0]))
        # calculate the angular positions relative to the candle using the arctan and the x and y offsets
        positions = np.append(positions, (np.degrees(np.arctan2(y, x))) % 360)
        return positions

    def posRelWhite(self, time: int) -> np.ndarray[float]:
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
        positions = (
            (360 / self.periods) * (time - self.refTimes) + self.refPositions
        ) % 360
        # positions[0] is white pos rel candle, add 180 to make it the candle pos rel white
        positions[0] = (positions[0] + 180) % 360
        return positions

    def getShadowPos(self, time: int) -> float:
        """Calculates the position of the shadow orb (moon equivalent) relative to
        the candle (earth equivalent).

        Parameters
        ---------
            time: `int`
                The epoch timestamp in ms at which the shadow orb position is calculated.
        Returns
        ---------
        `float`
            The position of the shadow orb relative to the candle at the passed in time argument
        """
        return (
            (360 / self.v["shadow"]["period"]) * (time - self.v["shadow"]["refTime"])
            + self.v["shadow"]["refOffset"]
        ) % 360

    def setRefPositions(self) -> None:
        """Calculates and stores the positions of each orb during their experimentally sampled
        reference times in self.refOffsets for future calculations.
        Updates variables.json to reflect these calculations
        """

        # note the shadow orb refOffset and refTime is experimentally gathered to
        # to calculate the refOffset of other orbs
        p = self.periods
        rt = self.refTimes
        ros = self.refOffsets
        shadow = self.v["shadow"]

        # the candle position is determined using aligments between the white orb and the shadow orb
        self.v["candle"]["refPos"] = (
            (360 / shadow["period"]) * (rt[0] - shadow["refTime"]) + shadow["refOffset"]
        ) % 360

        # the rest of the orbs are determined using alignments between the white orb and the orb in question
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
        """Gets the stored periods from self.v and packages them in an array to more easily parse.

        Returns
        ---------
        `np.ndarray[int]`
            An array with each element corresponding to the time in milliseconds it takes for
            the candle or respective orb to complete a full revolution around the white orb.
        """
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
        """Gets the stored radii from self.v and packages them in an array to more easily parse.

        Returns
        ---------
        `np.ndarray[float]`
            An array with each element corresponding to the radius in AU of each orb from the white orb.
        """
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
        """Gets the stored reference times for the candle and each orb from self.v
        and packages them in an array to more easily parse.

        Returns
        ---------
        `np.ndarray[int]`
            An array with each element corresponding to the reference epoch timestamp in ms for the candle or an orb.
        """
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
        """Gets the stored reference position for the candle and each orb from self.v
        and packages them in an array to more easily parse.

        Returns
        ---------
        `np.ndarray[float]`
            An array with each element corresponding to the reference position in degrees for the candle or an orb.
        """
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
        """Gets the stored reference position offset for the candle and each orb from self.v
        and packages them in an array to more easily parse.

        *Note: the offset will always be 0, 180, or 360 degrees based on whether or not the reference time alignment
        was a same side or opposite side alignment*

        Returns
        ---------
        `np.ndarray[float]`
            An array with each element corresponding to the reference position offset in degrees for the candle or an orb.
        """
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

    def saveCache(self, fileLoc: Path) -> None:
        """Saves the scroll event cache a JSON file.

        Parameters
        ---------
            fileLoc: `Path`
                The path to the JSON file the event cache data will be saved to.
        """
        json_object = json.dumps(self.scrollEventsCache, indent=4)
        with open(fileLoc, "w") as outfile:
            outfile.write(json_object)

    def updateVariables(self) -> None:
        """Overwrites the JSON file containing the orb variables with the current
        variables object (self.v)
        """
        json_object = json.dumps(self.v, indent=4)
        with self.variablesFile.open("w") as outfile:
            outfile.write(json_object)

    def getVariables(self, variablesFile: Path) -> dict[str, dict]:
        """Gets the orb variabes from a local JSON file.

        Parameters
        ---------
            variablesFile: `Path`
                The path to the JSON file that the orb variables are saved to.

        Returns
        ---------
            `dict[str, dict]`
                A dictionary containing variable information about the orbs
        """
        variables = {}
        with variablesFile.open("r") as json_file:
            variables = json.load(json_file)
        return variables

    # # used to update the event cache at set intervals (may slightly improve accuracy) instead of when
    # # an event is requested outside of the cache range, not actively used in prod
    # def autoRefreshCache(self, refreshRate:int=60 * 60 * 12):
    #     """Updates variables with any more recent and reference times received then automatically re-calculate
    #     event the cache. Should Be used with an asnychronous wrapper.

    #     Parameters
    #     ---------
    #         refreshRate: `int`
    #             The time interval in seconds between event cache recalculations
    #     """
    #     while True:
    #         #time.sleep(refreshRate)
    #         self.updateRefTimes()
    #         self.createScrollEventRange(
    #             startTime=(time.time() * 1000) - 2 * 86400000,
    #             stopTime=(time.time() * 1000) + 12 * 86400000,
    #             saveToCache=True
    #         )
    #         print("New Cache Last Item:", self.scrollEventsCache[-1])
    #         time.sleep(60*3)

    def updateScrollCache(self, start: int, stop: int) -> None:
        """Updates the reference time and position of each orb and overwrites the current
        scroll event cache with a new one.

        Parameters
        ------------
        start: `int`
            The epoch time in ms that alignment calculations will start from for the new cache.
        stop: `int`
            The epoch time in ms that alignment calculations will stop at for the new cache.
        """
        self.updateRefTimes()
        self.createScrollEventRange(startTime=start, stopTime=stop, saveToCache=True)
        # print("New Cache Last Item:", self.eventsCache[-1])

    def updateMoonCache(self, start: int, numMoonCycles: int) -> None:
        """Updates the reference time and position of each orb and overwrites the current
        scroll event cache with a new one.

        Parameters
        ------------
        start: `int`
            The epoch time in ms that alignment calculations will start from for the new cache.
        numMoonCycles: `int`
            The number of syndonic months that are calculated.
        """
        self.updateRefTimes()
        self.moonCyclesCache = self.createLunarCalendar(start, numMoonCycles)

    def updateRefTimes(self) -> None:
        """Parses newRefTimes.json which may contain more recent reference times for the orbs.
        Screens new reference times to make sure they're within an expected range and updates the variables
        and variables.json file to reflect the new valid reference times.
        """
        newVars: dict[str, list[int]] = {}
        with self.newRefTimeFile.open("r") as f:
            newVars = json.load(f)

        for orb in newVars:
            compOrb = orb if orb != "white" else "candle"
            # Check if current ref time is most recent refTime and check that it's within an expected alignment time range
            if (
                self.v[compOrb]["refTime"]
                != (newVars[orb][0] + newVars[orb][1] - 500) / 2
            ) and self.checkValidRefTime(orb, newVars[orb]):
                # average two times then subtract the total average time the events are off by
                eventTime = round((newVars[orb][0] + newVars[orb][1] - 500) / 2)
                posistions = self.posRelWhite(eventTime)
                if orb == "white":
                    orb = "candle"
                indicies = {
                    "candle": 0,
                    "black": 1,
                    "green": 2,
                    "red": 3,
                    "purple": 4,
                    "yellow": 5,
                    "cyan": 6,
                    "blue": 7,
                }
                orbPos = posistions[indicies[orb]]
                candlePos = posistions[indicies["candle"]]
                # check if orb and candle are on same or opposite sides
                refOffset = min(
                    [0, 180, 360], key=lambda x: abs(x - (orbPos - candlePos))
                )
                if refOffset == 360:
                    refOffset = 0
                # update variables
                self.v[orb]["refTime"] = eventTime
                self.v[orb]["refOffset"] = refOffset
        # reset arrays used to calculate events
        self.periods = self.getPeriods()
        self.radii = self.getRadii()
        self.refTimes = self.getRefTimes()
        self.refOffsets = self.getRefOffsets()
        self.setRefPositions()
        self.refPositions = self.getRefPositions()
        # Update the variables file to match the new refTimes
        self.updateVariables()

    def checkValidRefTime(self, orb: str, refTimes: list[int]) -> bool:
        """Creates a small scroll event cache overlapping the first refTime in order to check if
        that refTime is within an expected range for that event to happen.

        Parameters
        ---------
            orb: `str`
                The name of the orb
            refTimes: `list[int]`
                A list of the new reference times in reverse chronological order
                for the passed in orb.

        Returns
        ---------
            `bool`
            True if the refTimes[0] is a valid reference time.
        """
        startRange = self.getScrollEventsInRange(
            startTime=refTimes[0] - 15000, endTime=refTimes[0] + 15000
        )
        endRange = self.getScrollEventsInRange(
            startTime=refTimes[1] - 15000, endTime=refTimes[1] + 15000
        )
        if len(startRange) == 0 or len(endRange) == 0:
            return False
        orb = orb.capitalize()
        # white orb position is determined from darks rather than glows
        validStart = False
        validEnd = False
        if orb == "White":
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
        return validStart and validEnd

    def createLunarCalendar(
        self, startTime: int, numMoonCycles: int
    ) -> list[tuple[int, dict[str, any]]]:
        """Creates a chronologically ordered `list` of `tuples` that each
        contain information about a moon phase change.

        Parameters
        ---------
            startTime: `int`
                The epoch time in ms for which events after will recorded
            numMoonCycles: `int`
                The number of events for each phase that will be recorded

        Returns
        ---------
            `list[tuple[int, dict[str, any]]]`
                A `list` of `tuples` containing the epoch time at which the moon phase change happens and
                a dictionary containing the name of the new phase and a discord timestamp for the event.
        """
        if numMoonCycles == 0:
            return []

        # 8 phases in one moon cycle plus almost full and almost new
        numEvents = numMoonCycles * 10
        # phases change at noon so we will increment from the previous noon by one aberoth day
        currentTime = self.getLastNoonTime(startTime)
        tempCache = []

        # phase is determined by the position of the white orb (sun equivalent)
        # and the shadow orb (moon equivalent) relative to the candle (earth equivalent)
        dayStartWPos = self.getWhitePos(currentTime)
        dayStartSPos = self.getShadowPos(currentTime)
        while len(tempCache) < numEvents:
            phase = ""
            nextPhase = ""
            nextNoonTime = currentTime + self.oneAberothDay
            dayEndWPos = self.getWhitePos(nextNoonTime)
            dayEndSPos = self.getShadowPos(nextNoonTime)

            # get the position of the moon from the perspective of the earth
            # in the frame of reference where the sun is fixed at 180 degrees relative to the earth
            lunarCycleStartPos = (dayStartSPos - dayStartWPos + 360) % 360
            lunarCycleEndPos = (dayEndSPos - dayEndWPos + 360) % 360

            # new moon occur on a night that the moon crosses the 360/0 degree threshold
            if (
                lunarCycleStartPos < 360
                and lunarCycleStartPos > 347.5
                and (lunarCycleEndPos > 360 or lunarCycleEndPos < 12.5)
            ):
                phase = "new"
                nextPhase = "waxing_crescent"
            # first quarter occurs on the night the moon cross 90 degrees
            elif lunarCycleStartPos < 90 and lunarCycleEndPos > 90:
                phase = "first_quarter"
                nextPhase = "waxing_gibbous"
            # full moon occurs on the night the moon cross 180 degrees
            elif lunarCycleStartPos < 180 and lunarCycleEndPos > 180:
                phase = "full"
                nextPhase = "waning_gibbous"
            # third quarter occurs on the night the moon cross 90 degrees
            elif lunarCycleStartPos < 270 and lunarCycleEndPos > 270:
                phase = "third_quarter"
                nextPhase = "waning_crescent"

            # since phases always occur sequentially, only the new, q1, full, and q3 phases need to be determined
            # note that the length of the other phases can change a full a aberoth day as their length is determined
            # by when four primary phases happen and end

            if phase != "":
                tempCache.append(
                    (
                        currentTime,
                        {
                            "phase": phase,
                            "discordTS": f"<t:{int(np.floor(currentTime/1000))}:D> <t:{int(np.floor(currentTime/1000))}:t>",
                            # "discordRelTS": f'<t:{np.floor(currentTime/1000)}:R>'
                        },
                    )
                )
                tempCache.append(
                    (
                        nextNoonTime,
                        {
                            "phase": nextPhase,
                            "discordTS": f"<t:{int(np.floor(nextNoonTime/1000))}:D> <t:{int(np.floor(nextNoonTime/1000))}:t>",
                            # "discordRelTS": f'<t:{np.floor(nextNoonTime/1000)}:R>'
                        },
                    )
                )
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
        previousPhase = ""
        if firstPhase == "new":
            previousPhase = "waning_crescent"
        elif firstPhase == "first_quarter":
            previousPhase = "waxing_crescent"
        elif firstPhase == "full":
            previousPhase = "waxing_gibbous"
        elif firstPhase == "third_quarter":
            previousPhase = "waning_gibbous"

        # tempCache.insert(0, previousPhase)
        # print(tempCache)
        return tempCache

    def getLastNoonTime(self, time: int) -> int:
        """Gets the time at which noon last occured in aberoth relative to the passed in time.

        Parameters
        ---------
            time: `int`
                The epoch time in ms for which the previous Aberoth noon will be found.

        Returns
        ---------
            `int`
                The epoch time in ms of the last Aberoth noon before the passed in time.
        """
        return time - ((time - self.noonRefTime) % self.oneAberothDay)

    def getWhitePos(self, time: int) -> float:
        """Gets the position of the white orb in degrees at the given time.

        Parameters
        ---------
            time: `int`
                The epoch time in ms for which the position of the white orb will be calculated.

        Returns
        ---------
            `float`
                The position of the white orb in degrees at the given time.
        """
        position = (
            (360 / self.periods[0]) * (time - self.refTimes[0]) + self.refPositions[0]
        ) % 360
        return position


def formatTime(milliseconds: int) -> str:
    """Takes in a length of time in milliseconds and formats it into h:m:s:ms format.

    Parameters
    ---------
        milliseconds: `int`
            The lenght of time to be formatted
    Returns
    ---------
        `str`
        The length of time in the format f"{hours:.0f}h {minutes:.0f}m {seconds:.0f}s {ms}ms"
    """
    # Convert milliseconds to seconds
    seconds = milliseconds // 1000
    # Calculate hours, minutes and seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    ms = milliseconds % 1000
    # Return formatted time string
    return f"{hours:.0f}h {minutes:.0f}m {seconds:.0f}s {ms}ms"


if __name__ == "__main__":
    startTime = time.time_ns() // 1_000_000
    ephermis = Ephemeris(
        start=round((time.time() * 1000) + -4 * 86400000),
        end=round((time.time() * 1000) + 35 * 86400000),
        numMoonCycles=8,
        multiProcess=True,
    )
    stopTime = time.time_ns() // 1_000_000
    print(
        f"{ephermis.numCores} cores; Execution time: {formatTime(stopTime-startTime)}"
    )
    # import timeit
    # execution_time = timeit.timeit("Ephemeris(start=round((time.time() * 1000) - 0 * 86400000), end=round((time.time() * 1000) + 365 * 86400000), numMoonCycles=8)", globals=globals(), number=1)
    # execution_time = timeit.timeit("Ephemeris.createLunarCalendar(startTime, 8)", globals=globals(), number=50)

    # print(execution_time)
