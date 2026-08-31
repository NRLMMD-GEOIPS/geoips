.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _best_practices:

GeoIPS Generalized Best Practices
=================================

There are many ways one can incorporate GeoIPS into their research or operational flow.
While the developers do not want to be prescriptivist, we do recommend a series
of best practices to ensure that your plugin development/deployment experience is as smooth as possible.
First, we will propose some generalized best practices to consider before developing a plugin,
followed by best practices to follow during development, during initial release/deployment,
and finally at the planned or unplanned EOL of your plugin. Future iterations of this document
will include best practices for operational and research use of GeoIPS.

Best Practices at Conception of your Plugin
-------------------------------------------

In general, try to leverage existing GeoIPS capabilities before developing your own plugins!

* One of the core functions of GeoIPS is to eliminate redundant development time. Leverage that!
* If a reader exists, but is missing a core functionality required for your development, consider the
  following options:

  * Reach out to the developer of the reader and request they add the feature(s) you are missing. Odds
    are good that if you need it, someone else probably will too!
  * Pull the plugin containing the reader and add the functionality yourself. Then, open a PR on the repo
    containing the plugin to merge your changes.
  * If all else fails and the reader is no longer actively maintained, create a local copy for your plugin
    and provide proper attribution somewhere in your repository (provided you're going to open source your
    plugin, of course.)

Try to make an effort to attend the weekly open-source meetings routinely and become an active
participant in the discussions! As a community-driven effort, GeoIPS thrives as more people
join in!

* This will ensure you're up to date on the latest developments and are aware of what's coming down
  the pipeline. See the first bullet point for why that's important!
* You can also make requests of folks that are developing plugins and products to consider sources
  you are interested in working with.

  * This means you may not have to do as much development work on any plugins you develop
  * This also works both ways-- you might be able to save a member of the community some effort,
    as well as drive some collaboration!
* You'll be able to provide guidance on the direction GeoIPS is heading, ensuring that it is robust
  and has broad spectrum utility.

  * One prominent example includes the efforts of Tim Olander and Tony Wimmers's provision of
    feedback during development of the plugin system. Their feedback helped shape our overall
    implementation of plugins, and included one of the first demonstrations of the system via ARCHER.
  * Another example includes the development efforts at CIRA by Evan Rose and Jeremy Solbrig, who,
    while working closely with the community, have helped shape the way users interact with GeoIPS
    from the lowest levels, to the highest levels.
* Lastly, you can share your success stories and drive interest in the plugins you are developing.

Best Practices During Development of your Plugin
------------------------------------------------

When you develop a plugin, it is best to BEGIN by following the coding and formatting standards
recommended by the GeoIPS developers to facilitate easy sharing and integration into the GeoIPS
infrastructure.

* Make sure that you're developing in your own repository and not on the GeoIPS main branch.
* Ensure your code is properly commented and legible for fellow developers. You never know how many
  emails you'll be able to prevent by explaining your logic in advance!
* Make sure you follow the standards and practices recommended for providing informative runtime
  messages, and that they are logged at the correct levels.

  * Be sure to include a healthy mix of INFO, INTERACTIVE, DEBUG, WARNING and ERROR-level messages!
* Consider running an automated system to monitor your code for formatting and potential security
  risks (e.g., SQL injection.)

  * check_code.sh is a GeoIPS built-in method for monitoring these!
  * This is especially crucial for your code to enter operations on controllsed systems e.g., FNMOC,
    NAVO.

Packages change frequently! Make sure you're always on the latest working branch of GeoIPS and
any plugins you are using before sharing your code!

* Sometimes interfaces are deprecated between versions-- it's easier for everyone if you make sure
  everything works on the latest version.

  * An upcoming GeoIPS 2.0 will retain backward functionality for most plugins, however we reserve
    the right to revoke that capability at any time.
* To that end, stay abreast of upcoming deprecations within non-GeoIPS packages used by your plugin.
  You never know when NumPy will finally make good on all those warnings you've been ignoring!

We strongly discourage developing new, core infrastructure for GeoIPS, including new interfaces
and subsystems.

* These kinds of developments have a strong chance of creating conflicts later on down the line that
  may be difficult to resolve against the main GeoIPS repository.
* If you identify a need for new, core functionality raise your concern/request in the weekly meetings.
  At best we may have an alternative option to recommend, and at worst you may be conscripted into
  developing the feature!

If your GeoIPS plugin contains ANY proprietary IP or other sensitive data, it is CRUCIALLY IMPORTANT
that you do not make any changes to the codebases of the main GeoIPS repository or any plugins you
are using!

* In general, we will reject most commits made the main GeoIPS repository
* If that chance exists that your repo will enter open source, ensure that you are not committing
  anything private or dangerous.

  * Check for things like private keys in the commits, small pieces of information that when
    combined could lead to spillage, nasty merge comments, etc.

Ensure that your code is performant and reasonably Pythonic. Nobody wants their code to be the
bottleneck in someone else's workflow!

* If your plugin includes C or Fortran-wrapped algorithms that's also okay! We support interfaces
  that use f2py, etc. You might consider converting to native Python later on down the line, but
  that's never going to be mandatory.

Include test scripts and archive the mininmum number of files required to test your plugin!

* Doing so provides your users a quick way to understand how your plugin is invoked.

  * We recommend passing explicit file inputs to the procflow rather than a directory to ensure
    exact testing.
* The ability of developers to validate their installation of your plugin is crucial.

  * To that end, consider including the final output images to be used in the <whatever we call
    the script that compares images>

Lastly, share your successes and struggles at the weekly open source meeting!

* If you're running into problems or have questions, this is one of the best ways to resolve them.

  * You can also join the GeoIPS slack to ask questions 24/7
* People may have good suggestions or more performant ways to accomplish your goals.
* People will love to see the pretty pictures you make.

Best Practices Before and After Deploying your Plugin
-----------------------------------------------------

While we can't control how your administrate your own repositories, or how you run
GeoIPS, we can make some suggestions!

When you commit to an internal or public-facing repository, make sure ownership and permissions are
controlled appropriately.

* Try to not let people freely merge code into your repository as it creates a security risk for
  you and anyone using your plugin.
* Establish review requirements early on, and ensure that commits and PRs are fully tested before
  being merged. Optionally (but ideally,) you'd test these on a fresh GeoIPS installation to catch
  any dependencies that may be missing.

  * This is a good time to again ensure you're developing on the most recent versions of the GeoIPS
    and plugins.
* Include documentation for your plugin!

  * You can use this repository's documentation as a standard.

The infrastructure for automated processing and scheduling of GeoIPS runs on your system is
outside the scope this documentation.

* We don't want to risk pigeonholing anyone or exposing our own internal systems.
* That said, in a future release we may make some basic repositories with simple database
  and automation packages available.
* In general, though, all you need is way to identify when new files are available and a way
  to automate the passing of those files to GeoIPS. There are myriad solutions from this ranging
  from simple (cron) to advanced (Cylc)

Let people know when your plugin is ready for release!

* Share the good news at the open source meetings! Give talks at conferences! Advertise as
  best as you can!

  * This is good for GeoIPS and good for you. You may wind up roping in new talent or find
    transition avenues you weren't aware of.

Finally, be reasonably available to support your plugin for end users.

* Try to be an active participant on your repository's issues board at minimum.
* Answer questions that people have and address issues they may be coming across.
* Communicate your planned update schedule (if any) and try to stick to it.

  * If you plan to deprecate features of your plugin or bring it to end-of-life (EOL,)
    be sure to announce that well in advance!

Best Practices for Deprecation/EOL of your Plugin
-------------------------------------------------

When your plugin crosses the rainbow bridge, due to loss of funding, personnel, or interest
consider the following:

* Announce the upcoming deprecation/EOL at the GeoIPS weekly open source meeting.
* Include in your plugin repository a notice of upcoming EOL.
* Establish a chain of ownership/maintenance if possible.

  * Have in place a method for another developer to take control of the repository
    for ongoing updates
  * Remove or automatically redirect the repository to one where active development
    of the plugin is ongoing
  * Failing the above, place a prominent warning banning that indicates active
    development of the plugin has ceased.

GeoIPS Best Practices for Operations
======================================
[COMING SOON]

GeoIPS Best Practices for Research
======================================
[COMING SOON]
