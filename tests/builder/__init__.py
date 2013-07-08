from tests.builder.btest import main

import logger.exceptions

logger.exceptions.handle_exceptions(main, sectionname = 'builder test')
