'''
Created on Apr 19, 2012

@author: Jimmy
'''

import os, sys, logging

logger = logging.getLogger('OpenScore')
logging.basicConfig(level=logging.WARNING,
              format='%(asctime)s %(name)-12s %(levelname)s: %(message)s',
              datefmt='%Y-%m-%d %H:%M:%S',
              filename='OpenScore.log',
              filemode='w')
#log_handler = logging.FileHandler('OpenScore.log')
#formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
#log_handler.setFormatter(formatter)
#logger.addHandler(log_handler)
#logger.setLevel(logging.WARNING)

from scorer.bowlingscorer import BowlingScorer

progname = sys.argv[0]
progdir = os.path.dirname(progname)
sys.path.append(os.path.join(progdir,'components'))

if __name__ == '__main__':
    try:
        app = BowlingScorer()
        app.main()
    except:
        logging.error("Exception encountered. OpenScore will now close:")
        logging.exception('')