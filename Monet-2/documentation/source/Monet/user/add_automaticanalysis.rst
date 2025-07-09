Add an automatic analysis
==========================

Adding an histogram which is obtained through an automatic analysis is done in the histo yaml files
that also describe pages in Monet, similarly to adding an :ref:`histogram in a page<Add a page>`. 
The syntax of the portion of the YAML file to include an histogram from the automatic analysis is:

.. code-block:: yaml

    - addparams: {}
      center_x: 0.
      center_y: 0.
      size_x: 0.5
      size_y: 1.
      creation: '2021-10-26'
      display_options:
        showtitle: RICH1 Pixel Map (Routing Bit Physics)
        palette: kCool
        label_x: 'x [mm]'
        label_y: 'y [mm]'
        drawpattern: R1_grid_excluded.root
      motherh: ''
      name: Operation/Rich1Rebin
      taskname: AutomaticAnalysis
      operation:
        type: RebinRichGeneral
        inputs: 
          - name: RICH/HitMapsPhys/Rich1/PixelMap
            taskname: RichMon
          - name: RICH/HitMapsPhys/Rich1/nHits
            taskname: RichMon
        scales: 
          - 1e-4
          - 1e-4
