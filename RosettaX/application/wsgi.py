# -*- coding: utf-8 -*-

from RosettaX.application.main import RosettaXApplication, configure_logging


configure_logging(debug=False, log_level="INFO")

application = RosettaXApplication(
    host="0.0.0.0",
    port=8050,
    open_browser=False,
    debug=False,
)

app = application.app
server = app.server