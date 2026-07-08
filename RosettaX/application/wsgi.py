# -*- coding: utf-8 -*-

import os

from RosettaX.application.main import RosettaXApplication, configure_logging
from RosettaX.utils.upload_limits import configure_max_upload_bytes


configure_logging(debug=False, log_level="INFO")
configure_max_upload_bytes(os.getenv("ROSETTAX_MAX_UPLOAD_SIZE"))

application = RosettaXApplication(
    host="0.0.0.0",
    port=8050,
    open_browser=False,
    debug=False,
)

app = application.app
server = app.server