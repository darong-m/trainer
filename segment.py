#!/usr/bin/python3
import os
import os.path
import sys
from argparse import ArgumentParser
from subprocess import Popen, PIPE
import utils
from myconfig import MyConfig


config = MyConfig()

#change cwd to the libpinyin data directory
libpinyin_dir = config.getToolsDir()
libpinyin_sub_dir = os.path.join(libpinyin_dir, 'data')
os.chdir(libpinyin_sub_dir)
#chdir done


def handleError(error):
    sys.exit(error)


def segmentOneText(infile, outfile, reportfile, fast):
    infilestatuspath = infile + config.getStatusPostfix()
    infilestatus = utils.load_status(infilestatuspath)
    if utils.check_epoch(infilestatus, 'Segment'):
        return

    #begin processing
    if fast:
        cmdline = ['../utils/segment/spseg', \
                       '-o', outfile, infile]
    else:
        cmdline = ['../utils/segment/ngseg', \
                       '-o', outfile, infile]

    subprocess = Popen(cmdline, shell=False, stderr=PIPE, \
                           close_fds=True)

    lines = subprocess.stderr.readlines()
    if lines:
        print('found error report')
        with open(reportfile, 'wb') as f:
            f.writelines(lines)

    os.waitpid(subprocess.pid, 0)
    #end processing

    utils.sign_epoch(infilestatus, 'Segment')
    utils.store_status(infilestatuspath, infilestatus)


def handleOneIndex(indexpath, fast):
    indexstatuspath = indexpath + config.getStatusPostfix()
    indexstatus = utils.load_status(indexstatuspath)
    if utils.check_epoch(indexstatus, 'Segment'):
        return

    #begin processing
    indexfile = open(indexpath, 'r')
    for oneline in indexfile.readlines():
        #remove tailing '\n'
        oneline = oneline.rstrip(os.linesep)
        (title, textpath) = oneline.split('#')

        infile = config.getTextDir() + textpath
        outfile = config.getTextDir() + textpath + config.getSegmentPostfix()
        reportfile = config.getTextDir() + textpath + \
            config.getSegmentReportPostfix()

        print("Processing " + title + '#' + textpath)
        segmentOneText(infile, outfile, reportfile, fast)
        print("Processed " + title + '#' + textpath)

    indexfile.close()
    #end processing

    utils.sign_epoch(indexstatus, 'Segment')
    utils.store_status(indexstatuspath, indexstatus)


def walkThroughIndex(path, fast):
    for root, dirs, files in os.walk(path, topdown=True, onerror=handleError):
        for onefile in files:
            filepath = os.path.join(root, onefile)
            if onefile.endswith(config.getIndexPostfix()):
                handleOneIndex(filepath, fast)
            elif onefile.endswith(config.getStatusPostfix()):
                pass
            else:
                print('Unexpected file:' + filepath)


if __name__ == '__main__':
    parser = ArgumentParser(description='Segment all raw corpus documents.')
    parser.add_argument('--indexdir', action='store', \
                            help='index directory', \
                            default=config.getTextIndexDir())

    parser.add_argument('--fast', action='store_const', \
                            help='Use spseg to speed up segment', \
                            const=True, default=False)

    args = parser.parse_args()
    print(args)
    walkThroughIndex(args.indexdir, args.fast)
    print('done')
