System Overview
===============

.. uml::
   :caption: System overview

   [Virtual machine] as vm <<C++>>
   [fbuilder] <<Python>>
   fbuilder -> vm: builds images for