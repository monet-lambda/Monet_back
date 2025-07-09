Add a page
===================

Histograms are displayed in 'pages' that are arranged in a tree structure. This structure and its content are
managed by files, in YAML format, saved in the git repository: http://gitlab.cern.ch/lhcb/histoyml, in the *main* branch.
Every file in the git repository represents a page with one or more histogram. Seven top folders are defined
in the repository, to define pages for the different modes of Monet:

* OfflineDQ, for offline data quality
* OnlineMon, for online monitoring plots
* SimDQ, for simulation data quality
* SprucingDQ
* Trends, for trend plots
* Run2Archive, where one finds the Run2 pages
* Run3Archive, to archive unused Run3 pages

To add a new page in MONET, one first needs to have right access to the git repository by being member of the
``histoyml-editor`` group. Requests to be added to the group can be made through 
`this link <https://groups-portal.web.cern.ch/group/08d983fc-00ba-4415-82d0-4e07af899c4b/details>`_.

Adding a new page consists in creating a ``.yml`` file with the format described here. Files can be added or edited also directly 
using the `gitlab editor <https://gitlab.cern.ch/-/ide/project/lhcb/histoyml/edit/main/-/>`_. Don't forget to click on the 
*commit* button to save your files. Once added to git, the changes can be seen immediately in Monet by clicking on the 
*Refresh Tree* button. In addition, after every commit to the git repository, the git folder in the Monet server is 
automatically updated `with a gitlab webhook <https://gitlab.cern.ch/lhcb/histoyml/-/hooks>`_. 

.. code-block:: YAML

    histograms:
      - center_x: 0      # coordinate of the bottom left corner of the plot, in fraction of the total page size (0 = left)
        center_y: 0.21 # coordinate of the bottom left corner of the plot, in fraction of the total page size (0 = bottom)
        display_options: {}   # display options (see list below)
        motherh: null  # name of the histogram on which to overlay
        name: ODINMon/ODIN/Bcids  # Name of the histogram published by the task
        name_fallback: ODINMon/ODIN/Bcids_old  #Optional: name of a fallback histogram in case the original histogram does not exists
        size_x: 0.43875 # coordinate of the top right corner of the plot, in fraction of the total page size (1 = right)
        size_y: 1   # coordinate of the top right corner of the plot, in fraction of the total page size (1 = top)
        taskname: ODINMon  # Name of the monitoring task
        description: Description of the histogram to display in the histogram documentation popup window (linked from the pagedoc)
      - center_x: 0.4775  # coordinate of the bottom left corner of the plot, in fraction of the total page size (0 = left)
        center_y: 0.1425  # coordinate of the bottom left corner of the plot, in fraction of the total page size (0 = bottom)
        display_options: {}  # display options (see list below)
        motherh: '' # name of the histogram on which to overlay
        name: ODINMon/ODIN/BXType  # Name of the histogram published by the task
        size_x: 0.97625  # coordinate of the top right corner of the plot, in fraction of the total page size (1 = right)
        size_y: 0.975  # coordinate of the top right corner of the plot, in fraction of the total page size (1 = top)
        taskname: ODINMon  # Name of the monitoring task
    pagedoc: Test  # Text to show in the page documentation area in Monet (see below for more informations)
    pagename: LHCOctoberBeamTest/ODIN  # Name of the page, displayed in the tree</verbatim>

The ``taskname`` for DIM histograms is the name of the task running in the monitoring farm. For a quantity in the WinCC database, 
the ``taskname`` should be ``WinCC/PROJECT`` where PROJECT is the name of the WinCC project where the quantity is archived. For a 
counter stored in the WinCC database (which will be displayed in a table instead of a plot, the ``taskname`` to use is 
``WinCCCounter/PROJECT``.

The name is the name of the histogram for a DIM histogram or the name of the archived datapoint for a WinCC or WinCCCounter task.

The ``name_fallback`` is the name of an histogram to use in history mode in case the original histogram is not found: it can be useful 
if an histogram is replaced by a new one which did not exist in previous runs.

The documentation of the page is in `markdown <https://www.markdownguide.org/basic-syntax/>`_. Figures can be included also, 
they should be placed in the folder ``/hist/Reference/figures``, accessible from the plus online machines for people members of 
the ``hstwriter`` computing group (membership can be requested from the online support) and included as ``/figures/file_name.png``.

For trend plots, the syntax is:

.. code-block:: YAML

    histograms:
      - center_x: 0      # coordinate of the bottom left corner of the plot, in fraction of the total page size (0 = left)
        center_y: 0.21 # coordinate of the bottom left corner of the plot, in fraction of the total page size (0 = bottom)
        display_options: {}   # display options (see list below)
        motherh: null  # name of the histogram on which to overlay
        size_x: 0.43875 # coordinate of the top right corner of the plot, in fraction of the total page size (1 = right)
        size_y: 1   # coordinate of the top right corner of the plot, in fraction of the total page size (1 = top)
        name: UTGlobalEffMon/h_nutlay
        taskname: ut_track_eff_pred_upg
        value: eff34 
        error: deff34
        badrun_file: UTMon/eff34_badruns.txt   # text file containing the run numbers to exclude from the plot
        description: Description of the histogram to display in the histogram documentation popup window (linked from the pagedoc)
    pagedoc: Test  # Text to show in the page documentation area in Monet (see below for more informations)
    pagename: LHCOctoberBeamTest/ODIN  # Name of the page, displayed in the tree</verbatim>

where ``name`` and ``taskname`` identify the property to display, ``value`` is used for the value to display and ``error`` the
error on the value. ``badrun_file`` is the name of a file containing the list of runs to exclude from the plot; the path
of the file is relative to ``/hist/References``. 

The display options for the histograms are given in the form:

.. code-block:: YAML
    
    display_options: {option1: value1, option2: value2 }

or as:

.. code-block:: YAML

    display_options:
      option1: value1
      option2: value2

with the options as:

.. list-table::
  :widths: 15 35
  :header-rows: 1
  
  * - Option
    - Possible values
  * - analysisresults 
    - | ``None`` (default: do not display analysis resutls), ``legend`` : display analysis results in 
      | legend 
  * - bin_labelsX
    - Alternate text for bin labels on the x axis
  * - bin_labelsY
    - Alternate text for bin labels on the y axis
  * - drawopts
    - | null (default = ``e``, with error bars), ``hist`` (no error bars as histogram), ``coltextz`` 
      | (for 2d histo), ``marker`` (only marker, without error bars),  ``e0`` (error bars including 
      | bins at 0).    
      | For trend plots: ``line`` (default), ``marker``, ``marker_with_errors`` or  ``skip_missing`` 
      | (to remove unused run or fill numbers).
  * - drawpattern
    - | name of a ROOT file containing a pattern to overlay on the histogram: `overlay_name`. 
      | This ROOT file must be placed in the directory /hist/Reference/{taskname}.
      | The naming scheme is based on run ranges: `overlay_name_NNNNNN_MMMMMM.root` 
      | set 999999 if there is no end run for the time being. 
      | If no range is given, the default `overlay_name.root` file is used.
  * - extraheight
    - | Value to add to the 2D histogram bin height in order to mask the lines between 
      | bins if wanted
  * - extrawidth
    - | Value to add to the 2D histogram bin width in order to mask the lines between 
      | bins if wanted
  * - fillcolor
    - histogram fill color, in ROOT numbering scheme `scheme <https://root.cern.ch/doc/master/classTColor.html>`_ 
  * - gridx
    - ``no`` (default), ``yes``
  * - gridy
    - ``no`` (default), ``yes``
  * - hoverfile
    - | name of a JSON file containing informations to display as hover on bins of 2D histograms.
      | This JSON file must be placed in the directory /hist/Reference/{taskname}.
      | It should contain an array of elements, each element describes the information to display
      | for every bin. 
      | The element is a dictionnary with fields: "bin_id" (the bin id), "bin_center" (the center of 
      | the bin), "hover_label" (a dictionnary of label, each item of the form "title": "data").
      | the tool tip will show then "title": "data".
  * - label_x
    - x axis label
  * - label_y 
    - y axis label
  * - label_z
    - z axis label
  * - hidelegend
    - ``True`` to hide legend in trend plots
  * - legendlocation
    - | position of legend (for superimposed plots, to be set for the motherh):
      | ``top_left``, ``top_center``, ``top_right`` (default), ``center_left``, ``center_center``,
      | ``center_right``, ``bottom_left``, ``bottom_center``, ``bottom_right``, ``top``, ``left``,
      | ``center``, ``right``, ``bottom``
  * - legendlocation_x 
    - position of legend in pixels from the bottom left corner of the plot, for x coordinate 
  * - legendlocation_y
    - position of legend in pixels from the bottom left corner of the plot, for y coordinate 
  * - legendfontsize
    - size of the text of the legend, in 'px': ``8px``, ``9px``, ... (default: ``13px``)
  * - legendalpha
    - | Transparency of the legend (between 0 and 1, 0 = fully transparent, 1 = no 
      | transparency)
  * - legendtext
    - | Text to display in the legend (if not set, use showtitle value, or the title of the 
      | histograms if showtitle is not defined)
  * - linecolor
    - line color in `ROOT numbering scheme <https://root.cern.ch/doc/master/classTColor.html>`_ (blue by default)
  * - logx
    - ``no`` (default), ``yes`` 
  * - logy 
    - ``no`` (default), ``yes``
  * - logz
    - ``no`` (default), ``yes``
  * - norm 
    - ``False`` or ``None`` (default), ``True`` (normalized to integral of histogram)
  * - palette
    - | Name of the palette for the 2D histogram colors (name of the `ROOT palette <https://root.cern.ch/doc/master/classTColor.html#C06>`_,  of the 
      | `bokeh palette <https://docs.bokeh.org/en/2.4.3/docs/reference/palettes.html>`_ or of the custom palette)
  * - prof
    - | ``None`` (default), ``x`` (draw profile histogram for a 2D histogram in x), ``y`` (draw profile 
      | histogram for a 2D histogram in y)
  * - ref
    - | reference histogram normalisation: ``null`` (default = scale to integral), ``AREA`` (scale 
      | to integral, identical to default), ``ENTR`` (scale to number of entries), ``NO_NORM`` (no 
      | normalization)
  * - refdrawopts
    - | ``null`` (default = ``e``, with error bars), ``hist`` (no error bars), ``e0`` (error bars including 
      | bins at 0)
  * - rotate_labelsX
    - | rotate labels of the x axis (``False``, ``True``) (the angle can be changed with the 
      | angle_labelsX option - default 1.2)
  * - rotate_labelsY
    - | rotate labels of the y axis (``False``, ``True``) (the angle can be changed with the 
      | angle_labelsY option - default 1.2)
  * - rotate_axes
    - rotate 1D plot to have x axis on the vertical side (``False`` - default, ``True``)
  * - showtitle
    - title of the plot to display
  * - showxaxismarks
    - show marks on x axis (``True`` - default, ``False``) 
  * - showyaxismarks
    - show marks on y axis (``True`` - default, ``False``)
  * - showxaxislabels
    - show text on x axis (``True`` - default, ``False``) 
  * - showyaxislabels 
    - show text on y axis (``True`` - default, ``False``)
  * - stats
    - show statistics legend (`ROOT scheme <https://root.cern.ch/doc/master/classTPaveStats.html#PS01>`_)
  * - xmax
    - maximum of the x axis 
  * - xmin 
    - minimum of the x axis
  * - ymax
    - maximum of the y axis
  * - ymin
    - minimum of the y axis
  * - zmax
    - maximum of the z axis
  * - zmin
    - minimum of the z axis 
  * - zmin_fraction
    - | minimum of the z axis set as a fraction of the maximum z of the histogram (has 
      | priority over zmin)

