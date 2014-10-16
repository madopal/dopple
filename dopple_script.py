#!/usr/bin/python

import os, sys
from decimal import *
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import matplotlib.patches as mpatches
import numpy
import subprocess

colors = [ 'red', 'blue', 'green', 'pink', 'brown', 'gray', 'orange', 'purple', 'gold', 'black', 'magenta', 'cyan' ]

colorIndex = 0

MB_UNITS = float(1000000)
GB_UNITS = float(1000000000)

def PlotFiles(filelist, axes):
    global colorIndex
    datasets = []
    lineCount = len(filelist)
    curRow = 0
    curCol = 0
    for line in filelist:
        print line
        graphData = LoadData(line.strip())
        labelParts = line.split(".")
        if '/' in labelParts[0]:
            graphLabel = labelParts[0].split('/')[-1]
        else:
            graphLabel = labelParts[0]
        if len(graphData[2]) > 0:
#                ax1 = plt.subplot2grid((3,3), (0,0), colspan=3)
            ax1 = axes[curCol][curRow]
#                ax1 = fig.add_subplot(grid[0], grid[1], grid[2])
#                ax1.set_xlabel("GB transferred", color='black')
#                ax1.set_ylabel("Seconds per transfer chunk", color='black')
            ax1.grid(True)
            ax1.plot(graphData[0], graphData[1], colors[colorIndex], label=graphLabel)
            ax1.locator_params(axis = 'y', nbins = 4)
            for tick in ax1.xaxis.get_major_ticks():
                tick.label.set_fontsize(6)
            for tick in ax1.yaxis.get_major_ticks():
                tick.label.set_fontsize(6)
                # specify integer or one of preset strings, e.g.
                #tick.label.set_fontsize('x-small')
#                    tick.label.set_rotation('vertical')
            for bytes, time in zip(graphData[0], graphData[1]):
                if Decimal(time) <= Decimal(0.0):
                    ax1.axvline(x=bytes, ymin=0, ymax=1, linewidth=1, color='green', alpha=0.5, ls='dashed')
            leg1 = ax1.legend(bbox_to_anchor=(1.01, 1.35), loc=1, fontsize=4)
            leg1.get_frame().set_alpha(0.5)

            ax2 = axes[curCol][curRow + 1]
#                ax2 = fig.add_subplot(grid[0], grid[1], grid[2])
            curCol = curCol + 1
#                ax2.set_xlabel("GB transferred", color='black')
#                ax2.set_ylabel("Seconds per transfer chunk", color='black')
            ax2.grid(True)
            ax2.plot(graphData[2], graphData[3], colors[colorIndex], label=graphLabel)
            ax2.locator_params(axis = 'y', nbins = 4)
            for bytes, time in zip(graphData[2], graphData[3]):
                if Decimal(time) <= Decimal(0.0):
                    ax2.axvline(x=bytes, ymin=0, ymax=1, linewidth=1, color='green', alpha=0.5, ls='dashed')
            for tick in ax2.xaxis.get_major_ticks():
                tick.label.set_fontsize(6)
            for tick in ax2.yaxis.get_major_ticks():
                tick.label.set_fontsize(6)
            leg2 = ax2.legend(bbox_to_anchor=(1.01, 1.35), loc=1, fontsize=4)
            leg2.get_frame().set_alpha(0.5)
#                colorIndex = colorIndex - 1
#                ax3 = fig.add_subplot(313)
#                ax3.plot(graphData[0], graphData[1], colors[colorIndex], label=labelParts[0] + "-read")
#                colorIndex = colorIndex + 1
#                ax3.plot(graphData[2], graphData[3], colors[colorIndex], label=labelParts[0] + "-write", alpha=0.5)

        else:
            plt.plot(graphData[0], graphData[1], colors[colorIndex], label=labelParts[0])
            plt.legend()

#            z = numpy.polyfit(transfer, times, 2)
#            p = numpy.poly1d(z)
#            plt.plot(times,p(times),"r--")

        colorIndex = colorIndex + 1

def CreateData(line, totalBytes):
    parts = line.split()
    if len(parts) == 3:
        time = float(parts[1])
        size = float(parts[2]) / GB_UNITS
        totalBytes = totalBytes + size
        type = 0

    if len(parts) == 4:
        time = float(parts[2])
        size = float(parts[3]) / GB_UNITS
        totalBytes = totalBytes + size
        type = int(parts[1]) - 1

    return time, totalBytes, type

def LoadData(filename):
    graphData = [[], [], [], []]
    times = []
    sizes = []
    bytesPerSec = []
    transferAmount = []
    totalTime = 0.0
    totalBytesRead = 0.0
    totalBytesWritten = 0.0
    i = 0
    with open(filename, 'r') as file:
        for line in file.readlines():
            if i % 2:
                time, totalBytesWritten, type = CreateData(line, totalBytesWritten)
                graphData[(type * 2)].append(totalBytesWritten)
                graphData[(type * 2) + 1].append(time)
            else :
                time, totalBytesRead, type = CreateData(line, totalBytesRead)
                graphData[(type * 2)].append(totalBytesRead)
                graphData[(type * 2) + 1].append(time)
            i = i + 1
#                totalTime = totalTime + float(parts[1])
#                times.append(totalTime)
#                times.append(float(parts[1]))
#                size = float(parts[2]) / GB_UNITS
#                sizes.append(size)
#                totalBytes = totalBytes + size
#                transferAmount.append(totalBytes)
#                if Decimal(parts[1]) > 0.0:
#                    bytesPerSec.append((int(parts[2]) / float(parts[1])))
#                    bytesPerSec.append((int(parts[2]) / float(parts[1])))
#                else:
#                    bytesPerSec.append(0)

    return graphData



def PlotEverything(filelist, graphFilename):
    #times, sizes, bytesPerSec, transferAmount = LoadData(sys.argv[1])
    #fig = plt.figure()
    fig, axes = plt.subplots(nrows=6, ncols=2)
    fig.text(0.25, 0.97, "Read", horizontalalignment='center')
    fig.text(0.75, 0.97, "Write", horizontalalignment='center')
    fig.text(0.01, 0.5, "time per transfer", fontsize = 10, rotation='vertical', verticalalignment='center')
    fig.text(0.5, 0.01, "GB transferred", fontsize = 10, horizontalalignment='center')
    fig.tight_layout()


    #dates,values = zip(*items)


    #plt.plot(times, sizes, 'o-')
    #plt.plot(transferAmount, times, '-')
    PlotFiles(filelist, axes)

    plt.savefig(graphFilename, dpi=300)


def RunTest(filename, opts):
    args = "./copy_test -f %s %s" % ( filename, opts)
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
#    print out
    return out.strip()

def CleanUp(list):
    for file in list:
        os.unlink(file)


data_filename = sys.argv[1]
graphFilename = sys.argv[2]
datafile_list = []
args = [ "-s -n", "-s -w", "-s -d", "-r -n", "-r -w", "-r -d" ]
count = 0
# run the copy, collecting the filenames
#args = ['./copy_test', '-f /home/flynn/devel/Parcel/test/big_data/parcelTest005.dat', '-s', '-d']
with open(data_filename, 'r') as datafile:
    for line in datafile.readlines():
        if ( count < len(args) ):

            datafile_list.append(RunTest(line.strip(), args[count]))
            count = count + 1
        else:
            print "Skipping %s" % line.strip()

# plot
PlotEverything(datafile_list, graphFilename)
CleanUp(datafile_list)
#datafile_list.append(RunTest("/home/flynn/devel/Parcel/test/large_data/parcelTest005.dat", "-s -n"))
#datafile_list.append(RunTest("/home/flynn/devel/Parcel/test/large_data/parcelTest005.dat", "-s -w"))
#datafile_list.append(RunTest("/home/flynn/devel/Parcel/test/large_data/parcelTest005.dat", "-s -d"))
#datafile_list.append(RunTest("/home/flynn/devel/Parcel/test/large_data/parcelTest005.dat", "-r -n"))
#datafile_list.append(RunTest("/home/flynn/devel/Parcel/test/large_data/parcelTest005.dat", "-r -w"))
#datafile_list.append(RunTest("/home/flynn/devel/Parcel/test/large_data/parcelTest005.dat", "-r -d"))

#args = "./copy_test -f /home/flynn/devel/Parcel/test/big_data/parcelTest005.dat -s -d"
#proc = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)
#(out, err) = proc.communicate()
#print "stdout:"
#print out
#print "stderr:"
#print err

# create the list file

# plot
#PlotEverything(listFile, graphFilename)


