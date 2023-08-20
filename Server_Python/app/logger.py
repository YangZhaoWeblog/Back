import logging

logging.basicConfig(filename='./server.log',
                        level=logging.DEBUG,
                        format='[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)
