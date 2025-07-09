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

// Needed to have a run number when submitting to ELOG
var online_run_number;

function update_displayfills_glyph(state) {
  var glyphs = {
    activated: "glyphicon-ok",
    deactivated: "glyphicon-remove"
  };

  var icon = $("#changeDisplayFillsModeIcon");
  icon.attr("class", "glyphicon " + glyphs[state]);
}

function init_displayfills_state_button() {
  var button = $("#changeDisplayFillsMode");

  var state = button.data("state");

  update_displayfills_glyph(state);
}

function change_displayfills_mode() {
  var button = $("#changeDisplayFillsMode");
  var current_state = button.data("state");

  var new_state = {
    deactivated: "activated",
    activated: "deactivated"
  }[current_state];

  $.ajax({
    async: true,
    type: "GET",
    url: "change_displayfills_state",
    data: { state: new_state },

    success: function() {
      update_displayfills_glyph(new_state);
      button.data("state", new_state);

      if (window.last_dashboard_node_id)
        document.getElementById(window.last_dashboard_node_id + "_anchor").click();
    },

    error: function(xhr, ajaxOptions, thrownError) {
      alert("/change_displayfills_state error:" + thrownError);
      set_status_field("", "danger");
    }
  });
}

$(document).ready(function() {
  init_displayfills_state_button();
  $("#changeDisplayFillsMode").click(function() {
    change_displayfills_mode();
  });
});
