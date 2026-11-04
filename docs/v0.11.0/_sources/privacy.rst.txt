Privacy policy
==============

Last updated: 26 October 2026

This policy describes data handling by RosettaX. When you run RosettaX locally,
the application server runs on your computer. If you use an instance hosted by
someone else, files and application data are processed on that operator's server;
ask the operator about their hosting, access, backups, and retention practices.

Files and calibration data
--------------------------

RosettaX reads the FCS files, metadata, calibration files, and settings you select
to perform calibration and analysis. Browser uploads are sent to the RosettaX
application server. In a local installation, this transfer stays between your
browser and your computer. The application does not send these file contents to
GitHub or IPinfo as part of the requests described below.

Uploaded copies are stored on the application server, by default under
``~/.rosettax/uploads``, including a ``staged`` subdirectory for streamed uploads.
Saved calibrations and exported results are also written to disk. Storage paths
may be configured by the operator. Do not assume that closing the browser deletes
these files; remove copies and outputs you no longer need from their storage
locations after stopping the application.

Browser storage and logs
------------------------

RosettaX uses browser local storage for the theme and saved profiles, and session
storage for runtime settings and workflow state. Clear the site's browser data
to remove browser-stored information. Clearing browser data does not remove
files saved on the application server.

Application logs may contain filenames, file paths, request information, and
diagnostic details. Review logs and exported files before sharing them in a
support request, especially when filenames or FCS metadata identify people.

Usage information
-----------------

RosettaX maintains counters for home-page visits, calibration application clicks,
and calibrated file counts. It can also record page-visit timestamps, IP addresses,
page paths, browser user agents, and IP-derived location and network organization.
Local, loopback, and private-address visits are excluded from the page-visit log
by default; ``ROSETTAX_TRACK_LOCAL_VISITS`` can enable them. This exclusion does
not disable the IPinfo requests described below or the aggregate counters.

The default storage is files on the application server: ``usage_metrics.json``
and ``visit_log.jsonl`` in the RosettaX application-data directory. On Windows,
this is normally ``%LOCALAPPDATA%/RosettaX``; on macOS,
``~/Library/Application Support/RosettaX``; on other systems,
``~/.local/share/RosettaX``. Operators can configure different file locations or
a PostgreSQL database. These records are not automatically sent to a central
RosettaX analytics service. No automatic expiry is configured for these records;
the operator controls their removal and any backups.

External services
-----------------

RosettaX makes the following network requests in addition to communication
between the browser and application server:

* The home page checks the GitHub API for the latest RosettaX version. GitHub
  receives the server's public IP address and request headers, including a
  RosettaX user agent.
* Page visits trigger an IPinfo lookup using the visitor IP address resolved by
  the application server. IPinfo receives that address and the server's public
  IP address. This lookup currently also occurs for local addresses, before
  local visits are excluded from logging. Results are cached in server memory.
* The home page includes a remotely hosted Zenodo badge. Loading it can disclose
  the browser's public IP address and normal browser request information to
  Zenodo. Following external links or downloading RosettaX also involves the
  respective website providers.

Those providers handle requests under their own privacy policies. A local
installation therefore should not be understood as making no internet requests.

Questions and requests
----------------------

For questions about RosettaX's data handling, contact the maintainer at
``martin.poinsinet.de.sivry@gmail.com``. For access to or deletion of information
on a hosted instance, contact that instance's operator. Avoid posting personal
information or sensitive experimental files in public GitHub issues.
