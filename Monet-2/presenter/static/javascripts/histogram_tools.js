/*****************************************************************************\
* (c) Copyright 2000-2020 CERN for the benefit of the LHCb Collaboration      *
*                                                                             *
* This software is distributed under the terms of the GNU General Public      *
* Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   *
*                                                                             *
* In applying this licence, CERN does not waive the privileges and immunities *
* granted to it by virtue of its status as an Intergovernmental Organization  *
* or submit itself to any jurisdiction.                                       *
\*****************************************************************************/
// Histogram tools

// Save recursively all the histograms
function saveAllHistograms() {
  var i = 0;
  $(".bk-root").each(function() {
    var run_number = $("#runNmbrTextfield").val();
  
    html2canvas(this,  {
      scale:1
    }).then((canvas) => {
      var file_name = "monet-" + run_number + "-" + this.id + ".png";
      var data_url = canvas.toDataURL("image/png");
  
      var evt_obj;
      var anchor = document.createElement("a");
      anchor.setAttribute("href", data_url);
      anchor.setAttribute("target", "_blank");
      anchor.setAttribute("download", file_name);
  
      if (document.createEvent) {
        evt_obj = document.createEvent("MouseEvents");
        evt_obj.initEvent("click", true, true);
        anchor.dispatchEvent(evt_obj);
      } else if (anchor.click) {
        anchor.click();
      }
    });
  });
}

function saveAllHistogramsAsSingleFile() {
  var run_number = $("#runNmbrTextfield").val();
  html2canvas(document.getElementById("main"),  {
    width: Math.max(document.getElementById("svg-canvas").scrollWidth,document.getElementById("pageheader").scrollWidth),
    height: document.getElementById("svg-canvas").scrollHeight+document.getElementById("pageheader").scrollHeight+60+document.getElementById("information-panel").offsetHeight,
    windowWidth: Math.max(document.getElementById("svg-canvas").scrollWidth+document.getElementById("pageheader").scrollWidth),
    windowHeight: document.getElementById("svg-canvas").scrollHeight+document.getElementById("pageheader").scrollHeight+60+document.getElementById("information-panel").offsetHeight,
    scrollX: -window.scrollX,
    scrollY: -window.scrollY
    }).then((canvas) => {
    var file_name = "monet-" + run_number + ".png";
    var data_url = canvas.toDataURL("image/png");

    var evt_obj;
    var anchor = document.createElement("a");
    anchor.setAttribute("href", data_url);
    anchor.setAttribute("target", "_blank");
    anchor.setAttribute("download", file_name);

    if (document.createEvent) {
      evt_obj = document.createEvent("MouseEvents");
      evt_obj.initEvent("click", true, true);
      anchor.dispatchEvent(evt_obj);
    } else if (anchor.click) {
      anchor.click();
    }
  });
}

