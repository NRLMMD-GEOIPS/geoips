 .. dropdown:: Distribution Statement

   | # # # Distribution Statement A. Approved for public release. Distribution unlimited.
   | # # #
   | # # # Author:
   | # # # Naval Research Laboratory, Marine Meteorology Division
   | # # #
   | # # # This program is free software: you can redistribute it and/or modify it under
   | # # # the terms of the NRLMMD License included with this program. This program is
   | # # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
   | # # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
   | # # # for more details. If you did not receive the license, for more information see:
   | # # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

.. _interface-doc-template:

*********************************************************
Template for Drafting Documentation for GeoIPS Interfaces
*********************************************************

*Short Introduction which introduces why we have this interface*

Could Include short summaries about:

#. Why the interface is needed
#. What benefits come from using this interface
#. Why you should care about this interface
#. What the interface does

When To Use This Interface
--------------------------

*In depth detail of when to use this interface within GeoIPS*

#. Include information about normal use cases of the interface
#. Include information about how it's used internally
#. Include information about corner cases and possible future uses

What The Interface Is
---------------------

*In depth information about what the interface actually is*

#. Is it a module or a yaml -based interface?
#. What does this module / yaml file actually define?

How To Use This Interface
-------------------------

*In depth detail how how to construct and use this interface*

Now that we know what the interface is, we can break it down even further so that users
can actually make use of this interface.

#. First, break down how to use this interface. Primarily, you'll want to describe how
   this interface is used in conjunction alongside other interfaces. For example, if you
   are writing documentation for the output checkers interface, you'll want to describe
   how this interface is used to test an output product. This output product will have
   been produced by some product (which could include a product defaults), a reader,
   algorithm, etc. Combined these plugins are used to create an output product which
   would be tested via an output checker.
#. Next, you'll want to describe how to create a plugin using this interface. Feel free
   to provide examples of plugins under this specific interface, and break down what
   each part of the plugin actually accomplishes. (``__call__`` if module, ``spec`` if
   yaml, ...). Once this is done, a user will be more familiar with the construction of
   a plugin of a certain interface. This way, they'll have a better idea to what they'll
   need to define to generate their desired output.

Motivation Behind This Interface / Benefits That Come From It
-------------------------------------------------------------

*In depth detail describing why we created this interface and what parts of GeoIPS
benefit from it's creation.*

#. Why we needed this interface
#. What benefits stem from its creation
