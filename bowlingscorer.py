'''
Created on Apr 19, 2012

@author: Jimmy
'''

import os, sys, logging
from scorer.log import *

#log_handler = logging.FileHandler('OpenScore.log')
#formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
#log_handler.setFormatter(formatter)
#logger.addHandler(log_handler)
#logger.setLevel(logging.WARNING)

from scorer.bowlingscorer import BowlingScorer

progname = sys.argv[0]
progdir = os.path.dirname(progname)
sys.path.append(os.path.join(progdir,'components'))
logger.info("Starting OpenScore...")
if __name__ == '__main__':
    try:
        #logging.info("Creating main BowlingScorer object...")
        app = BowlingScorer()
        #logging.info("Entering run loop...")
        app.main()
    except:
        logger.info("Exception encountered. OpenScore will now close:")
        logger.exception('')