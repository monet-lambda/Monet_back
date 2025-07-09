Add a reference histogram
-----------------------------------------

Online references
+++++++++++++++++

Reference histograms for the task `MyTask` are stored in the directory `/hist/Reference/MyTask`. 
There might be more than one root file in the directory. The name of the root file containing 
the histogram must be `default_1.root` in order to be picked up by Monet. The easiest to provide a 
reference histogram is to copy a root file of a saveset from a good run that you can find in the 
directory `/hist/Savesets/ByRun/MyTask`. The features listed below for OfflineDQ are also available 
for the online and history modes.

References for OfflineDQ
++++++++++++++++++++++++

The reference histograms for OfflineDQ are separate from the Online ones to include histograms by HLT2. 
They are stored in `/hist/OfflineDQ/Reference/MyTask`.

References for OfflineDQ should follow a naming scheme that is based on run ranges: `reference_NNNNNN_MMMMMM.root`, 
for example `reference_277879_277891.root`, where the first and the last run are included in the range that the reference is used for.

Special run numbers: the first run number in Run3 is **232278**, and **999999** is a run number that signals 
that no end run is known, and the reference is valid for future runs.

DQ contacts are responsible for selecting references and their bookkeeping. It is recommended to make an enty 
in the logbook when changing reference files, and to rename the previously used file in case run number 999999 
has been used.

Deprecated naming shemes
^^^^^^^^^^^^^^^^^^^^^^^^

Naming shemes based on TCK, ACTIVITY or other identifiers are kept for backward compatibility, but their use is 
discuraged from 2024 onwards, as a run is the smallest entity capturing all relevant information retrievable 
through the RunDB.

For older runs, not covered by the run-range scheme, Monet will first look for references based on TCK, then 
ACTIVITY.  The reference name can be extended by additional identifiers, separated by 
`_<IdentifierName>=<Value>` like `=reference_TCK=0x12345678_Mu=1.1.root`. Other identifiers could be 
Mag(=Up,Down), Align(=v90).

Write permissions
+++++++++++++++++

In order to be able to write in the `/hist` directory, you have to ask the online support to be in the Linux 
`hstwriter` group.