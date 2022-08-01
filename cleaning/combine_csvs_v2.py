# combine all _min csvs for study 2 & 3 into 1 giant megafile for analysis


import pandas as pd
import os

start = "asist-data-sharing/output/resampled"
outputFolder = "asist-data-sharing/output"


def combineCSVs(directory):
    # get {minute files}
    minuteFiles = set()
    for filename in os.listdir(directory):
        if filename.endswith("min.csv"):
            minuteFiles.add(filename)
        else:
            continue
    print(f"Total trials: {len(minuteFiles)}")


    dfMegafile = pd.DataFrame()

    counter = 0
    for minuteFile in minuteFiles:
        counter += 1
        print(f"{counter} / {len(minuteFiles)}")
        # get min df
        dfmin = pd.read_csv(directory + os.sep + minuteFile)

        # parse out interventions at time interval -1 from dfmin
        timeDeltaInterval = str(pd.to_timedelta((-1 // 1000) // 60, 'min'))
        value = dfmin.at[dfmin.tail(1).index[0], 'time']
        if value == timeDeltaInterval:
            print("Dropping.")
            dfmin.drop(dfmin.tail(1).index[0], inplace=True)

        # combine min df with megafile
        dfMegafile = pd.concat([dfMegafile, dfmin], sort=False)

    # dfMegafile.to_csv(outputFolder + os.sep + 'combined_megafile.csv')
    return dfMegafile


def run():
    dfUltraMegafile = pd.DataFrame()
    directory = start
    miniMegafile = combineCSVs(directory)
    dfUltraMegafile = pd.concat([dfUltraMegafile, miniMegafile], sort=False)

    dfUltraMegafile.to_csv(outputFolder + os.sep + 'combined_megafile.csv')


run()
print("Done.")
