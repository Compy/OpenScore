'''
Created on Jul 16, 2012

@author: compy
'''
import os, sys, logging

logger = logging.getLogger('OpenScore')
logging.basicConfig(level=logging.INFO,
      format='%(asctime)s %(name)-12s %(levelname)s: %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S',
      filename='OpenScore.log',
      filemode='w')
        