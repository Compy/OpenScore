'''
Created on Apr 19, 2012

@author: Jimmy
'''

import os, sys

from scorer.bowlingscorer import BowlingScorer

progname = sys.argv[0]
progdir = os.path.dirname(progname)
sys.path.append(os.path.join(progdir,'components'))

if __name__ == '__main__':
    app = BowlingScorer()
    app.main()