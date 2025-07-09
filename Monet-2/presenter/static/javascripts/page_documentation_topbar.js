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
export function save_as_pdf() {
    html2canvas(document.getElementById("svg-canvas"),  {
        height: document.getElementById("svg-canvas").scrollHeight+document.getElementById("pageheader").scrollHeight+60,
        windowHeight: document.getElementById("svg-canvas").scrollHeight+document.getElementById("pageheader").scrollHeight+60,
        scrollY: -window.scrollY
        }).then((canvas) => {
        var file_name = "documentation.png";
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
    