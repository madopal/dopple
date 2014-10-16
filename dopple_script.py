#!/usr/bin/python

import os, sys
from decimal import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import matplotlib.patches as mpatches
import numpy
import subprocess

colors = [ 'red', 'blue', 'green', 'pink', 'brown', 'gray', 'orange', 'purple', 'gold', 'black', 'magenta', 'cyan' ]

colorIndex = 0

MB_UNITS = float(1000000)
GB_UNITS = float(1000000000)

DEFAULT_GRAPHNAME = "plot.png"

SIZE_B = 1.0
SIZE_KB = 1024.0
SIZE_MB = 1.0e6
SIZE_GB = 1.0e9
SIZE_TB = 1.0e12
SIZE_PB = 1.0e15

LABEL_B  = "B"
LABEL_KB = "KB"
LABEL_MB = "MB"
LABEL_GB = "GB"
LABEL_TB = "TB"
LABEL_PB = "PB"

byteScales = {
    'B': SIZE_B,
    'KB': SIZE_KB,
    'MB': SIZE_MB,
    'GB': SIZE_GB,
    'TB': SIZE_TB,
    'PB': SIZE_PB
}

def PrintHelp():
    cmdLineParts = sys.argv[0].split('/')
    for elements in cmdLineParts:
        if elements.find(".py"):
            scriptName = elements

    print ""
    print "** %s **" % scriptName
    print "A program to copy files and get performance data from the copy"
    print ""
    print "usage: %s [options]" % scriptName
    print "Options:"
    print "  --filename [FILENAME] - filename of list file for data (mandatory to run, 6 files should be given)"
    print "  --graphname [FILENAME] - filename of output graph (defaults to %s, will overwrite existing)" % DEFAULT_GRAPHNAME
    print "  --graphonly - only does the graphing, using the filename as a list of files to graph"
    print "  --help - this help"

    return

def DebugPrint(string, verbose):
    if verbose:
        print string

    return

def ParseCommandLineArgs():
    isOk = False
    verbose = False
    findall = False
    graphonly = False
    filename = ""
    graphname = DEFAULT_GRAPHNAME

    # temp flags
    gettingFilename = False
    gettingGraphname = False

    if len(sys.argv) >= 2:
        for arg in sys.argv:
            if not arg.find("--"):
                if not arg.find("--help"):
                    PrintHelp()
                elif not arg.find("--filename"):
                    gettingFilename = True
                elif not arg.find("--graphname"):
                    gettingGraphname = True
                elif not arg.find("--graphonly"):
                    graphonly = True
                elif not arg.find("--Belgium"):
                    print "** Watch your language! **"
            else:
                if gettingFilename:
                    filename = arg.strip()
                    gettingFilename = False
                if gettingGraphname:
                    graphname = arg.strip()
                    gettingGraphname = False

    if (len(filename) > 0):
        isOk = True

    return isOk, filename, graphname, graphonly

def GetScale(bytes):

    label = ""
    size = 0

    if bytes < SIZE_KB:
        label = LABEL_B
    elif bytes < SIZE_MB:
        label = LABEL_KB
    elif bytes < SIZE_GB:
        label = LABEL_MB
    elif bytes < SIZE_TB:
        label = LABEL_GB
    elif bytes < SIZE_PB:
        label = LABEL_TB
    else:
        label = LABEL_PB

    return label


def PlotFiles(filelist, axes):
    global colorIndex
    datasets = []
    lineCount = len(filelist)
    curRow = 0
    curCol = 0
    for line in filelist:
        graphData, readScale, writeScale = LoadData(line.strip())

        if line.strip().find("seq") != -1:
            graphLabel = "sequential"
        else:
            graphLabel = "random"

        if line.strip().find("nore") != -1:
            graphLabel = graphLabel + ", noreuse"
        elif line.strip().find("will") != -1:
            graphLabel = graphLabel + ", willneed"
        else:
            graphLabel = graphLabel + ", dontneed"

#        labelParts = line.split(".")
#        if '/' in labelParts[0]:
#            graphLabel = labelParts[0].split('/')[-1]
#        else:
#            graphLabel = labelParts[0]
        if len(graphData[2]) > 0:
#                ax1 = plt.subplot2grid((3,3), (0,0), colspan=3)
            ax1 = axes[curCol][curRow]
#                ax1 = fig.add_subplot(grid[0], grid[1], grid[2])
            totalTime = sum(graphData[1])
#            print graphData[1]
            ax1.set_xlabel("%.03f %s in %.03f sec" % (graphData[0][-1], readScale, totalTime), color='black', fontsize=5)
#            ax1.set_ylabel("Seconds per transfer chunk", color='black', fontsize=5)
            ax1.grid(True)
            if len(graphData[0]) < 15:
                markerType = '.'
            else:
                markerType = ''
            ax1.plot(graphData[0], graphData[1], colors[colorIndex], label=graphLabel, marker=markerType)
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
#            print
#            print graphData[3]
            totalTime = sum(graphData[3])
#            ax2.set_xlabel("GB transferred", color='black', fontsize=5)
            ax2.set_xlabel("%.03f %s in %.03f sec" % ( graphData[2][-1], writeScale, totalTime), color='black', fontsize=5)
#            ax2.set_ylabel("Seconds per transfer chunk", color='black', fontsize=5)
            ax2.grid(True)
            if len(graphData[2]) < 15:
                markerType = '.'
            else:
                markerType = ''
            ax2.plot(graphData[2], graphData[3], colors[colorIndex], label=graphLabel, marker=markerType)
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

def CreateData(line, totalBytes, totalTime, scale):
    parts = line.split()
    if len(parts) == 3:
        time = float(parts[1])
        size = float(parts[2]) / float(byteScales[scale])
        totalBytes = totalBytes + size
        totalTime = totalTime + time
        type = 0

    if len(parts) == 4:
        time = float(parts[2])
        size = float(parts[3]) / float(byteScales[scale])
        totalBytes = totalBytes + size
        totalTime = totalTime + time
        type = int(parts[1]) - 1

    return time, totalTime, totalBytes, type

def FindScale(file):
    readBytes = 0
    writtenBytes = 0

    for line in file.readlines():
        parts = line.split()
        if len(parts) == 3:
            if int(parts[2]) > writtenBytes:
                writtenBytes = int(parts[2])

        if len(parts) == 4:
            if (int(parts[1]) - 1) == 0:
                if int(parts[3]) > readBytes:
                    readBytes = int(parts[3])
            else:
                if int(parts[3]) > writtenBytes:
                    writtenBytes = int(parts[3])


    readScale = GetScale(readBytes)
    writeScale = GetScale(writtenBytes)

    return readScale, writeScale


def LoadData(filename):
    graphData = [[], [], [], []]
    times = []
    sizes = []
    bytesPerSec = []
    transferAmount = []
    totalTimeRead = 0.0
    totalTimeWritten = 0.0
    totalBytesRead = 0.0
    totalBytesWritten = 0.0
    i = 0
    with open(filename, 'r') as file:
        readScale, writeScale = FindScale(file)
        file.seek(0)
        for line in file.readlines():
            if i % 2:
                time, totalTimeWritten, totalBytesWritten, type = CreateData(line, totalBytesWritten, totalTimeWritten, writeScale)
                graphData[(type * 2)].append(totalBytesWritten)
                graphData[(type * 2) + 1].append(time)
            else :
                time, totalTimeRead, totalBytesRead, type = CreateData(line, totalBytesRead, totalTimeRead, readScale)
                graphData[(type * 2)].append(totalBytesRead)
                graphData[(type * 2) + 1].append(time)
            i = i + 1
    return graphData, readScale, writeScale


def PlotEverything(filelist, graphFilename):
    fig, axes = plt.subplots(nrows=6, ncols=2)
    fig.text(0.25, 0.97, "Read", horizontalalignment='center')
    fig.text(0.75, 0.97, "Write", horizontalalignment='center')
    fig.text(0.01, 0.5, "time per transfer", fontsize = 10, rotation='vertical', verticalalignment='center')
    fig.text(0.5, 0.01, "data transferred", fontsize = 10, horizontalalignment='center')
    fig.tight_layout()
    PlotFiles(filelist, axes)
    plt.savefig(graphFilename, dpi=300)


def RunTest(filename, opts):
    args = "./dopple -f %s %s" % ( filename, opts)
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
#    print out
    return out.strip()


def CleanUp(list):
    for file in list:
        os.unlink(file)

def CheckForDopple():
    rc = 0
    if not os.path.exists("dopple"):
        makeProc = subprocess.Popen("make", stdout=subprocess.PIPE)
        streamdata = makeProc.communicate()[0]
        rc = makeProc.returncode
    else:
        print "Executable present"

    return rc

isOk, data_filename, graph_filename, graphonly = ParseCommandLineArgs()
datafile_list = []
args = [ "-s -n", "-s -w", "-s -d", "-r -n", "-r -w", "-r -d" ]
count = 0
# run the copy, collecting the filenames
if isOk:
    if CheckForDopple() == 0:
        if graphonly == False:
            with open(data_filename, 'r') as datafile:
                for line in datafile.readlines():
                    if ( count < len(args) ):
                        datafile_list.append(RunTest(line.strip(), args[count]))
                        count = count + 1
                    else:
                        print "Skipping %s" % line.strip()
        else:
            with open(data_filename, 'r') as datafile:
                for line in datafile.readlines():
                    datafile_list.append(line.strip())

        # plot
        PlotEverything(datafile_list, graph_filename)
        CleanUp(datafile_list)
    else:
        print "Unable to build executable, exiting"
else:
    PrintHelp()
