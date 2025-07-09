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

// Reads out global variables set by python program and sets toolbar icons accordingly
var online_run_number;

window._refresh_enabled = false;
var _refresh_rate = 60000;

function do_refresh() {
  if (!window._refresh_enabled) return;

  reload_page(true);
}

function reload_page(refresh) {
  var url = "/online_dq";
  url +=
    "?selected_page=" + $(".jstree-container-ul").jstree("get_selected")[0];
  url += "&partition=" + $("#partition-field").val();

  if (refresh) url += "&refresh=true";

  window.location.href = url;
  set_rundb_info();
}

function enable_refresh() {
  window._refresh_enabled = true;
  var icon = $("#refresh-icon");
  icon.attr("class", "glyphicon glyphicon-stop");
  $("#refresh-text").text("Stop refreshing");

  setTimeout(do_refresh, _refresh_rate);
}

function disable_refresh() {
  window._refresh_enabled = false;
  var icon = $("#refresh-icon");
  $("#refresh-text").text("Start refreshing");

  icon.attr("class", "glyphicon glyphicon-play");
}

function set_rundb_info() {
  // For online, this should be the latest run in the partition var run_number = $("#runNmbrTextfield").val();

  $.ajax({
    async: true,
    type: "GET",
    url: "/rundb?mode=online&partition="+$("#partition-field").val(),

    success: function(server_reply) {
      if (!server_reply.success) return;

      var popover = $("#runInfo").data("bs.popover");
      popover.options.html = true;
      popover.options.sanitize = false;
      popover.options.content = server_reply.rundb_info;

      online_run_number = server_reply.rundb_info.match(
        /rundb-run-number\"\>(\d+)\</
      )[1];

      var popover_is_visible = $("#runInfo")
        .data("bs.popover")
        .tip()
        .hasClass("in");
      if (popover_is_visible) {
        $("#runInfo").popover("show");
      }
    }
  });
}

$(function() {
  init_reference_state_button();

  $("#changeReferenceMode").click(function() {
    change_reference_mode();
  });
  $("#pageRefresh").click(function() {
    if (window._refresh_enabled) disable_refresh();
    else enable_refresh();
  });

  var refresh = getUrlParameter("refresh");
  if (refresh) {
    enable_refresh();
  }

  var select = document.getElementById("partition-field");
  select.addEventListener("change", function() {
    reload_page(false);
  });

  $('#runInfo').on('show.bs.popover', function() {
    $.ajax({
      async: false,
      type: "GET",
      url: "/rundb?mode=online&partition="+$("#partition-field").val(),
  
      success: function(server_reply) {
        if (!server_reply.success) return;
        
        var popover = $("#runInfo").data("bs.popover");
        popover.options.html = true;
        popover.options.sanitize = false;
        popover.options.content = server_reply.rundb_info;
  
        online_run_number = server_reply.rundb_info.match(
          /rundb-run-number\"\>(\d+)\</
        )[1];
  
//        var popover_is_visible = $("#runInfo")
//          .data("bs.popover")
//          .tip()
//          .hasClass("in");
//        if (popover_is_visible) {
//          $("#runInfo").popover("show");
//        }
      }
    });

  })

  //set_rundb_info();
});
