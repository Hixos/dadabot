import logging
import os

logger = logging.getLogger('dadabot')

if 'PORT' in os.environ:
    logging.basicConfig(filename='dadabot.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s:\t%(message)s')

logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
