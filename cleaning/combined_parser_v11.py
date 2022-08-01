### TO DO ###
# 1. make sure the imported modules are installed (os, ast, pandas, numpy, dateutil)
# 2. download .metadata files into a folder
# 3. set directory variable to path location of folder containing metadata files (from Step 2)
#    if on Mac, right click on folder, hold down the option key, then click "copy 'folderName' as Pathname"
#    if on Windows, right click on folder, hold down shift key, then click "Copy as path"
# 4. create a folder to store generated .csv files
# 5. set outputFolder variable to path location of designated output folder (from Step 4)
#    (same as in step 3)
# 6. set timeInterval variable to desired resampling time interval (1S, 10S, 15S, 1min, or 30min [for the whole session])
# 7. download the external data file linking trial/team to condition ID, agent name, and map order
# 8. set externalDataFile variable to path location of downloaded external data file
#    (same as in step 3)
# 9. set study variable to the correct study (asist2 or asist3)
# 10. if running interventions, download uaz intervention file & set uazInterventionFile to the file path
# 11. run this file!


import os
import ast
import string
import pandas as pd
import numpy as np
from dateutil.parser import parse


directory = 'asist-data-sharing/data'  # no / at the end
outputFolder = 'asist-data-sharing/output'
timeInterval = '1min'  # min = minute, S = second
study = "asist3"

externalDataFile = 'ASIST Study 3 Info - current.csv'

includeInterventions = False
uazInterventionFile = "uaz_interventions.csv"  # only if includeIntervetions


# reads the external data file and outputs {trial: {"externalVar": externalVarContent}}
def parseExternalDataFile(filepath):
    file = open(filepath, 'r')
    lines = file.readlines()
    result = {}

    firstLine = True
    for line in lines:
        if firstLine:
            firstLine = False
            continue
        vars = line[:-1].split(",")
        conditionID, agentName, teamID, trialID1, trialID2, mapOrder = vars
        result[trialID1] = {"conditionID": conditionID, "agentName": agentName, "teamID": teamID, "trialID":
            trialID1, "mapOrder": mapOrder}
        result[trialID2] = {"conditionID": conditionID, "agentName": agentName, "teamID": teamID, "trialID":
            trialID2, "mapOrder": mapOrder}

    return result


# take in intervention content, outputs intervention type
# (only works for certain cmu teams due to inconsistent format across teams)
def getInterventionType(interventionContent):
    interventionType = ""
    interventions = {
        "I am PSI-Coach, an Automated Advisor!": "Introduction",
        "Keep on placing markers": "Encourage After First Marker",
        "Keep going!": "Encourage After Intervention Gap",
        "You just missed marking": "Victim Presence Marker Placement",
        "Consider prioritizing the critical victim rooms": "Prioritize Critical Victims",
        "Apply more of your": "Inappropriate Skill Use",
        "Be sure to use the room marker": "Follow Victim Presence Marker",
        "Consider checking in with the": "Victim Strategy Verification",
        "Sync up with the": "Victim Strategy Alignment",
        "Great job adapting your behavior!": "Encourage After Avoidance"
    }

    for key in interventions:
        if interventionContent.startswith(key):
            interventionType = interventions[key]

    return interventionType


# takes uaz team's intervention data file and outputs {trial: interventionData}
def parseUazInterventions():
    trials = {}
    interventionData = {"startTime": [], "interventionType": [], "interventionContent": [], "globalTime": []}

    file = open(uazInterventionFile, 'r')
    lines = file.readlines()
    currTrial = ""
    for line in lines:
        splitLine = line.split(",")
        elapsedTime, globalTime, team, trial, interventionType = splitLine[:5]
        interventionContent = ",".join(splitLine[5:-1])
        target = splitLine[-1]  # not used right now but might be necessary for future analysis

        if elapsedTime == "elapsed_time":  # skip if header row
            continue

        elif trial == currTrial:
            startTime = round(pd.to_timedelta(elapsedTime, 'min').total_seconds() * 1000)  # convert time to ms
            interventionData["startTime"].append(startTime)
            interventionData["interventionType"].append(interventionType)
            interventionData["interventionContent"].append(interventionContent)
            interventionData["globalTime"].append(globalTime)
        else:
            if currTrial: trials[currTrial] = interventionData
            interventionData = {"startTime": [], "interventionType": [], "interventionContent": [], "globalTime": []}
            startTime = round(pd.to_timedelta(elapsedTime, 'min').total_seconds() * 1000)  # convert time to ms
            interventionData["startTime"].append(startTime)
            interventionData["interventionType"].append(interventionType)
            interventionData["interventionContent"].append(interventionContent)
            interventionData["globalTime"].append(globalTime)
            currTrial = trial

    trials[currTrial] = interventionData  # add info for last trial
    return trials


# sync up uaz intervention timestamp with this parser's elapsed_ms (edits dict in-place)
def syncTimes(interventionData, globalToElapsedMs):
    thisGlobal, thisElapsedMs = globalToElapsedMs

    for i in range(len(interventionData["globalTime"])):
        globalTime = interventionData["globalTime"][i]

        actualElapsedTime = parse(globalTime) - parse(thisGlobal)
        actualStartTime = round(pd.to_timedelta(actualElapsedTime, 'min').total_seconds() * 1000) + thisElapsedMs

        interventionData["startTime"][i] = actualStartTime


def run():
    overallCounter = 0
    totalFiles = len(os.listdir(directory))

    externalData = parseExternalDataFile(externalDataFile)

    # uaz intervention stuff
    if includeInterventions:
        uazInterventionData = parseUazInterventions()

    hasInterventions = []  # dummy variable to store which trials use the "Intervention:Chat" format

    # iterate through all the files
    for filename in os.listdir(directory):

        overallCounter += 1
        print(f"PROGRESS: {overallCounter} / {totalFiles}")

        # checking if it is a metadata file
        if not filename.endswith(".metadata"):
            continue

        file = open(directory + os.sep + filename, 'r')
        trialStart = filename.index("Trial-T") + len("Trial-")
        trial = filename[trialStart:trialStart+7]
        teamStart = filename.index("Team-T") + len("Team-")
        team = filename[teamStart:teamStart+8]
        print(f"Trial: {trial}, Team: {team}")

        doneOnes = {('TM000212', 'T000623'), ('TM000326', 'T000852'), ('TM000312', 'T000823'), ('TM000227', 'T000654'), ('TM000219', 'T000637'), ('TM000289', 'T000777'), ('TM000222', 'T000643'), ('TM000309', 'T000818'), ('TM000269', 'T000738'), ('TM000232', 'T000664'), ('TM000207', 'T000613'), ('TM000260', 'T000720'), ('TM000320', 'T000839'), ('TM000279', 'T000758'), ('TM000261', 'T000722'), ('TM000317', 'T000833'), ('TM000319', 'T000838'), ('TM000217', 'T000634'), ('TM000236', 'T000672'), ('TM000246', 'T000691'), ('TM000311', 'T000821'), ('TM000229', 'T000657'), ('TM000310', 'T000819'), ('TM000278', 'T000755'), ('TM000294', 'T000788'), ('TM000245', 'T000690'), ('TM000275', 'T000750'), ('TM000284', 'T000767'), ('TM000238', 'T000675'), ('TM000277', 'T000754'), ('TM000268', 'T000735'), ('TM000216', 'T000632'), ('TM000322', 'T000844'), ('TM000202', 'T000603'), ('TM000211', 'T000621'), ('TM000217', 'T000633'), ('TM000305', 'T000810'), ('TM000272', 'T000744'), ('TM000314', 'T000827'), ('TM000231', 'T000661'), ('TM000267', 'T000733'), ('TM000210', 'T000619'), ('TM000255', 'T000710'), ('TM000266', 'T000731'), ('TM000214', 'T000628'), ('TM000270', 'T000740'), ('TM000283', 'T000765'), ('TM000274', 'T000747'), ('TM000302', 'T000804'), ('TM000319', 'T000837'), ('TM000225', 'T000649'), ('TM000233', 'T000666'), ('TM000327', 'T000853'), ('TM000303', 'T000805'), ('TM000244', 'T000687'), ('TM000273', 'T000745'), ('TM000296', 'T000791'), ('TM000250', 'T000700'), ('TM000328', 'T000855'), ('TM000276', 'T000751'), ('TM000214', 'T000627'), ('TM000318', 'T000836'), ('TM000327', 'T000854'), ('TM000325', 'T000850'), ('TM000255', 'T000709'), ('TM000229', 'T000658'), ('TM000233', 'T000665'), ('TM000275', 'T000749'), ('TM000238', 'T000676'), ('TM000329', 'T000858'), ('TM000273', 'T000746'), ('TM000231', 'T000662'), ('TM000235', 'T000670'), ('TM000290', 'T000779'), ('TM000218', 'T000635'), ('TM000227', 'T000653'), ('TM000276', 'T000752'), ('TM000288', 'T000776'), ('TM000314', 'T000828'), ('TM000303', 'T000806'), ('TM000281', 'T000762'), ('TM000293', 'T000786'), ('TM000290', 'T000780'), ('TM000330', 'T000859'), ('TM000252', 'T000703'), ('TM000246', 'T000692'), ('TM000326', 'T000851'), ('TM000307', 'T000814'), ('TM000210', 'T000620'), ('TM000216', 'T000631'), ('TM000292', 'T000783'), ('TM000298', 'T000796'), ('TM000241', 'T000682'), ('TM000329', 'T000857'), ('TM000328', 'T000856'), ('TM000311', 'T000822'), ('TM000237', 'T000674'), ('TM000262', 'T000723'), ('TM000284', 'T000768'), ('TM000325', 'T000849'), ('TM000260', 'T000719'), ('TM000248', 'T000696'), ('TM000205', 'T000609'), ('TM000294', 'T000787'), ('TM000270', 'T000739'), ('TM000234', 'T000668'), ('TM000257', 'T000713'), ('TM000206', 'T000611'), ('TM000302', 'T000803'), ('TM000265', 'T000729'), ('TM000258', 'T000715'), ('TM000297', 'T000793'), ('TM000331', 'T000862'), ('TM000299', 'T000797'), ('TM000259', 'T000717'), ('TM000261', 'T000721'), ('TM000324', 'T000848'), ('TM000239', 'T000677'), ('TM000291', 'T000782'), ('TM000226', 'T000652'), ('TM000298', 'T000795'), ('TM000228', 'T000655'), ('TM000271', 'T000742'), ('TM000269', 'T000737'), ('TM000316', 'T000831'), ('TM000307', 'T000813'), ('TM000293', 'T000785'), ('TM000242', 'T000684'), ('TM000267', 'T000734'), ('TM000331', 'T000861'), ('TM000235', 'T000669'), ('TM000256', 'T000712'), ('TM000218', 'T000636'), ('TM000211', 'T000622'), ('TM000205', 'T000610'), ('TM000313', 'T000826'), ('TM000301', 'T000801'), ('TM000219', 'T000638'), ('TM000318', 'T000835'), ('TM000239', 'T000678'), ('TM000271', 'T000741'), ('TM000266', 'T000732'), ('TM000268', 'T000736'), ('TM000323', 'T000845'), ('TM000234', 'T000667'), ('TM000308', 'T000816'), ('TM000226', 'T000651'), ('TM000306', 'T000812'), ('TM000249', 'T000697'), ('TM000309', 'T000817'), ('TM000243', 'T000685'), ('TM000202', 'T000604'), ('TM000248', 'T000695'), ('TM000259', 'T000718'), ('TM000253', 'T000705'), ('TM000289', 'T000778'), ('TM000203', 'T000606'), ('TM000203', 'T000605'), ('TM000228', 'T000656'), ('TM000249', 'T000698'), ('TM000282', 'T000763'), ('TM000306', 'T000811')}


        if (team, trial) in doneOnes:
            print("Already done.")
            continue

        Lines = file.readlines()

        # reset BEARD dict
        BEARD = {}

        # dictionary that will accumulate the ted values
        TED = {
            'process_effort_s': [],
            'process_skill_use_s': [],
            'process_workload_burnt': [],
            'comms_total_words': [],
            'comms_equity': [],
            'triage_count': [],
            'team_score': [],
            'elapsed_ms': [],  # elapsed_milliseconds
            'team_score_agg': []
        }

        # dictionary with structure {color: ID}, e.g., {"Green": "E000606"}
        players = {}

        if includeInterventions:
            # reset intervention dict
            interventionData = {"startTime": [], "interventionType": [], "interventionContent": []}

            # check if uaz (already parsed uaz interventions)
            isUaz = False
            if trial in uazInterventionData:
                interventionData = uazInterventionData[trial]
                isUaz = True
            globalToElapsedMs = ()

        # iterates over the messages in the metadata
        for line in Lines:

            try:
                curr = ast.literal_eval(line)  # convert current line to dictionary

                if includeInterventions and not isUaz and curr["msg"]["sub_type"] == "Intervention:Chat":  # check for chat interventions
                    # receivers = curr["data"]["receivers"]  # list of players receiving intervention
                    interventionData["startTime"].append(curr["data"]["start"])  # intervention start time in ms (since beginning of session)
                    interventionContent = curr["data"]["content"]  # intervention message
                    interventionData["interventionContent"].append(interventionContent)
                    interventionType = getInterventionType(interventionContent)
                    interventionData["interventionType"].append(interventionType)

                if curr['msg']['source'] == 'ac_cmu_ta2_beard' and curr['data']['team']:  # check if message comes from beard, add it it has team data
                    BEARD = curr['data']
                elif curr['msg']['source'] == 'ac_cmu_ta2_ted':  # check if message comes from ted
                    for key in TED:
                        TED[key].append(curr['data'][key])  # append ted values to the dictionary
                    if includeInterventions and isUaz and not globalToElapsedMs and "header" in curr and "timestamp" \
                            in curr["header"] and TED["elapsed_ms"]:
                        # get (timestamp, elapsed_ms) so uaz timestamp can be sync'd with this parser's elapsed_ms
                        globalToElapsedMs = (curr["header"]["timestamp"], TED["elapsed_ms"][-1])
                elif curr['data']['participant_id'] and curr['data']['callsign'] and len(players) < 3:  # get participant id of players until there are 3
                    players[curr['data']['callsign']] = curr['data']['participant_id']
            except:
                continue

        df = pd.DataFrame.from_dict(TED)  # get dataframe from dictionary

        # infer number of critic victims from team score
        df['critic_victim'] = np.floor(df['team_score'].divide(50))
        df['noncritic_victim'] = df['team_score'] - df['critic_victim']*50
        df['noncritic_victim'].divide(10)

        # add Beard values and participant ids to dataframe
        for key in BEARD:
            reversePlayers = {playerID: playerColor for playerColor, playerID in players.items()}
            newKey = key
            for metric in BEARD[key]:
                # make key format consistent between teams (reformat to be COLOR_metric)
                for color in ["RED", "GREEN", "BLUE"]:
                    if key.startswith(color):
                        newKey = color
                if key.startswith("E"):
                    newKey = reversePlayers[key].upper()
                col = newKey + '_' + metric
                df[col] = BEARD[key][metric]
        for player in players:
            df[player] = players[player]
        df['team'] = team
        df['trial'] = trial

        # store dataframe
        nombre = outputFolder + os.sep + "metadata" + os.sep + filename
        df.to_csv(nombre+'.csv')

        # offset
        offset = df.iloc[0]['elapsed_ms']
        df['elapsed_ms'] = df['elapsed_ms']-offset

        # convert milliseconds to datetype column to aggregate values
        df['time'] = pd.to_timedelta(df['elapsed_ms'], 'ms')

        # aggregate values correctly over desired frequency
        meanAggs = ['process_effort_s', 'process_skill_use_s', 'process_workload_burnt', 'comms_equity',
                    'comms_total_words', 'triage_count']
        maxAggs = ['elapsed_ms', 'team_score_agg']
        sumAggs = ['critic_victim', 'noncritic_victim', 'team_score']

        df_mean = df[meanAggs + ['time']]
        df_max = df[maxAggs + ['time']]
        df_sum = df[sumAggs + ['time']]

        df_mean = df_mean.set_index(df['time']).resample(timeInterval).mean()
        df_max = df_max.set_index(df['time']).resample(timeInterval).max()
        df_sum = df_sum.set_index(df['time']).resample(timeInterval).sum()

        df = df.set_index(df['time']).resample(timeInterval).first()  # base aggregation function = take 1st value

        for meanVar in meanAggs:
            df[meanVar] = df_mean[meanVar]
        for maxVar in maxAggs:
            df[maxVar] = df_max[maxVar]
        for sumVar in sumAggs:
            df[sumVar] = df_sum[sumVar]

        df['team'] = team
        df['trial'] = trial

        df['filename'] = filename
        df['study'] = study


        # change time index to "aggregate" for aggregation row (if timeInterval is '30min')
        if timeInterval == "30min":
            if df.shape[0] == 1:  # check that the output only has 1 row (it should represent the entire session)
                oldIndex = pd.to_timedelta("0", 'min')
                df.rename(index={oldIndex: 'aggregate'}, inplace=True)
            else:
                print(f"ERROR: Aggregation csv for trial {trial} over time interval {timeInterval} has > 1 row.")

        # add external data
        df["condition-id"] = ""
        df["condition-agent-name"] = ""
        df["map-order"] = ""
        if trial in externalData:
            df["condition-id"] = externalData[trial]["conditionID"]
            df["condition-agent-name"] = externalData[trial]["agentName"]
            df["map-order"] = externalData[trial]["mapOrder"]
        else:
            print(f"ERROR: External data file missing team {team}, trial {trial}.")

        # add intervention data (only if not aggregating across whole session)
        if includeInterventions and timeInterval != "30min":
            numInterventions = 1  # how many interventions there are in the set timeInterval
            df[f"intervention_type_{numInterventions}"] = np.nan
            df[f"intervention_content_{numInterventions}"] = np.nan

            if len(interventionData["startTime"]) > 0:
                hasInterventions += [(team, trial)]

            # sync up uaz intervention timestamp with this parser's elapsed_ms
            if isUaz: syncTimes(interventionData, globalToElapsedMs)

            print("NUM INTERVENTIONS", len(interventionData["startTime"]))
            # loop through all interventions
            for i in range(len(interventionData["startTime"])):

                # round intervention start time to nearest time interval (floored)
                startTime = interventionData["startTime"][i]
                roundedStartTime = startTime // 1000  # time to the nearest sec (rounded down)
                if timeInterval == "1min":
                    roundedStartTime = roundedStartTime // 60  # time to nearest min (rounded down)
                    timeDelta = pd.to_timedelta(roundedStartTime, 'min')
                elif timeInterval == "30min":
                    roundedStartTime = roundedStartTime // 60  # time to nearest min (rounded down)
                    roundedStartTime = 30 * (roundedStartTime // 30)
                    timeDelta = pd.to_timedelta(roundedStartTime, 'min')
                else:
                    if timeInterval == "15S":
                        roundedStartTime = 15 * (roundedStartTime // 15)
                    elif timeInterval == "10S":
                        roundedStartTime = 10 * (roundedStartTime // 10)
                    # otherwise, timeInterval == 1S
                    timeDelta = pd.to_timedelta(roundedStartTime, 'sec')

                interventionType = interventionData["interventionType"][i]
                interventionContent = interventionData["interventionContent"][i]

                if timeDelta in df.index:  # check if rounded start time is already a row in the dataframe
                    if not pd.isnull(df.at[timeDelta, "intervention_content_1"]):  # check if there's already an intervention at the rounded start time
                        written = False
                        for j in range(1, numInterventions+1):  # see if there's already an empty duplicate intervention col
                            if not written and pd.isnull(df.at[timeDelta, f"intervention_content_{j}"]):
                                df.loc[timeDelta, [f"intervention_type_{j}", f"intervention_content_{j}"]] = [
                                    interventionType, interventionContent]
                                written = True
                        if not written:  # create more columns for more duplicate interventions as needed
                            numInterventions += 1
                            df[f"intervention_type_{numInterventions}"] = np.nan
                            df[f"intervention_content_{numInterventions}"] = np.nan
                            df.loc[timeDelta, [f"intervention_type_{numInterventions}", f"intervention_content_{numInterventions}"]] = [interventionType, interventionContent]

                    else:  # since this is the 1st intervention at the rounded time, just add intervention info into the row
                        df.loc[timeDelta, [f"intervention_type_1", "intervention_content_1"]] = [interventionType,
                                                                                                 interventionContent]
                else:  # create a new row since the rounded time isn't already a row in the dataframe
                    print(f"ERROR: Intervention time stamp not included for {timeDelta}")
                    totalCols = df.shape[1]
                    df.loc[timeDelta] = [np.nan]*(totalCols-2*numInterventions) + [interventionType] + [interventionContent] \
                                        + [np.nan]*(numInterventions - 1)*2

        nombre = outputFolder + os.sep + "resampled" + os.sep + filename
        if timeInterval == "30min":
            df.to_csv(nombre + '_min_aggregate.csv')
        else:
            df.to_csv(nombre+'_min.csv')


run()


print("Done.")


