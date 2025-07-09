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
var req_data;

function init_status_indicator() {
  if (filename == "") {
    set_status_field("Filename not provided!", "warning");
  } else if (reference_filename == "") {
    set_status_field("Reference Filename not provided!", "warning");
  }
}

function set_request_id() {
  var req_id = $("#runNmbrTextfield").val();
  disable_nav_bar(false);
  if (req_id == "0") return;
  var request_url = new URLSearchParams(window.location.href);
  var previous_event_type = request_url.get('prev_event_type');
  var prev_sim_hist_file = request_url.get('prev_sim_hist_file');
  $.ajax({
    async: true,
    type: "GET",
    url: "set_request_id",
    data: {
      reqid: req_id
    },

    success: function (json) {
      if (!json.success) {
        alert(json.data);
        return;
      }
      req_data = json.data
      // Populate event types
      $.each(req_data, function (index, value) {
        $("#evtSelect").append(`<option>${index}</option>`);
        if (index == previous_event_type) {
          $("#evtSelect").val(index).change();
        }
      });
      // // Populate file names with currently selected event type
      var event_type = $("#evtSelect").val();
      $.each(req_data[event_type], function (index, value) {
        $("#fileSelect").append(`<option>${value}</option>`);
        if (value == prev_sim_hist_file) {
          $("#fileSelect").val(value).change();
        }
      });
    },

    error: function (xhr, ajaxOptions, thrownError) {
      alert("/set_request_id error:" + thrownError);
      //set_status_field("", "danger");
    },

    complete: function () {
      set_rundb_info();
      disable_nav_bar(false);
    }
  });
}

function init_req_id_icon() {
  var passed_req_id = unescape(getUrlParameter("run_number"));
  if (passed_req_id != "undefined")
    $("#runNmbrTextfield").val(passed_req_id);

  if ($("#runNmbrTextfield").val() != "") {
    set_request_id();
  }
}

function set_new_request_id(req_id) {
  var url = "browse_req?";
  url += "run_number=" + req_id;
  url += "&prev_event_type=" + $("#evtSelect").val();
  url += "&prev_sim_hist_file=" + $("#fileSelect").val();
  url += "&reference_state=" + $("#changeReferenceMode").data("state");
  url += "&selected_page=" + $(".jstree-container-ul").jstree("get_selected")[0];
  window.location.href = url;
}

function increase_request_id() {
  // Check field is populated
  // Make request to api
  // Set field to id response
  if ($("#runNmbrTextfield").val() != "") {
    var reqid = parseInt($("#runNmbrTextfield").val());
    $.ajax({
      async: true,
      type: "GET",
      url: "get_next_request_id?reqid=" + reqid,

      success: function (json) {
        if (!json.success) {
          alert(json.data);
          $("#increaseRequestIdButton").prop("disabled", true);
          return;
        }
        set_new_request_id(json["data"]["reqid"]);
        $("#runNmbrTextfield").val(json.data.reqid)
      },

      error: function (xhr, ajaxOptions, thrownError) {
        alert("Run switch error:" + thrownError);
        set_status_field("JSON Error:" + thrownError, "danger");
      },
      complete: function () {
        disable_nav_bar(false);
      }
    });
  }
}

function decrease_request_id() {
  // Check field is populated
  // Make request to api
  // Set field to id response
  if ($("#runNmbrTextfield").val() != "") {
    var reqid = parseInt($("#runNmbrTextfield").val());
    $.ajax({
      async: true,
      type: "GET",
      url: "get_previous_request_id?reqid=" + reqid,

      success: function (json) {
        if (!json.success) {
          alert(json.data);
          $("#decreaseRequestIdButton").prop("disabled", true);
          return;
        }
        set_new_request_id(json["data"]["reqid"]);
        $("#runNmbrTextfield").val(json.data.reqid)
      },

      error: function (xhr, ajaxOptions, thrownError) {
        alert("Run switch error:" + thrownError);
        set_status_field("JSON Error:" + thrownError, "danger");
      },
      complete: function () {
        disable_nav_bar(false);
      }
    });
  }
}

function latest_request_id() {
  $.ajax({
    async: true,
    type: "GET",
    url: "get_latest_request_id",

    success: function (json) {
      if (!json.success) {
        alert(json.data);
        return;
      }
      set_new_request_id(json["data"]["reqid"]);
      $("#runNmbrTextfield").val(json.data.reqid)
    },

    error: function (xhr, ajaxOptions, thrownError) {
      alert("Run switch error:" + thrownError);
      set_status_field("JSON Error:" + thrownError, "danger");
    },
    complete: function () {
      disable_nav_bar(false);
    }
  });
}

function oldest_request_id() {
  $.ajax({
    async: true,
    type: "GET",
    url: "get_oldest_request_id",

    success: function (json) {
      if (!json.success) {
        alert(json.data);
        return;
      }
      set_new_request_id(json["data"]["reqid"]);
      $("#runNmbrTextfield").val(json.data.reqid)
    },

    error: function (xhr, ajaxOptions, thrownError) {
      alert("Run switch error:" + thrownError);
      set_status_field("JSON Error:" + thrownError, "danger");
    },
    complete: function () {
      disable_nav_bar(false);
    }
  });
}

function obj_to_table_rows(obj) {
  let table_rows;
  try {
    table_rows = Object.keys(obj).filter((key) => key !== "success").map((key) => {
      let content = obj[key];
      if (content == null) {
        content = "null";
      }
      if (typeof content === "object") {
        return obj_to_table_rows(content);
      } else {
        return `<tr> <td><b>${key}</b></td> <td>${content}</td> </tr>`;
      }
    }).flat();
  } catch (e) {
    console.error(e);
    return undefined;
  }
  return table_rows;
}

function obj_to_table(obj) {
  let table_rows;
  try {
    table_rows = obj_to_table_rows(obj).join("\n");
  } catch (e) {
    console.error(e);
    return `<table class="table"><table>`;
  }
  return `<table class="table">${table_rows}<table>`;
}

function set_rundb_info() {
  const run_number = $("#runNmbrTextfield").val();
  $.ajax({
    async: true,
    type: "GET",
    url: "get_req_info",
    data: {
      reqid: $("#runNmbrTextfield").val(),
      eventType: $("#evtSelect").val(),
      simHistFile: $("#fileSelect").val()
    },

    success: function (server_reply) {
      let popover = $("#runInfo").data("bs.popover");
      if (!server_reply.success) return;

      const table_content = obj_to_table(server_reply);
      popover.options.html = true;
      popover.options.sanitize = false;
      popover.options.content = table_content;

      const popover_is_visible = $("#runInfo")
        .data("bs.popover")
        .tip()
        .hasClass("in");
      if (popover_is_visible) {
        $("#runInfo").popover("show");
      }
    }
  });
}

////////////////////////////////////////////
//jQuery part
////////////////////////////////////////////

$(function () {
  // Initialise selections
  init_status_indicator();
  init_reference_state_button();
  init_req_id_icon();
  // Keycode 13 corresponds to typing enter
  $("#runNmbrTextfield").keypress(function (e) {
    if (e.keyCode == 13) {
      set_new_request_id($("#runNmbrTextfield").val());
      return false;
    }
  });

  set_status_field("", "success");
  $("#changeReferenceMode").click(function () {
    change_reference_mode();
  });

  $("#increaseRequestIdButton").click(function () {
    increase_request_id()
  });
  $("#decreaseRequestIdButton").click(function () {
    decrease_request_id()
  });
  $("#latestRequest").click(function () {
    latest_request_id()
  });
  $("#oldestRequest").click(function () {
    oldest_request_id()
  });
  // Go button
  $("#setReqButton").click(function () {
    set_new_request_id($("#runNmbrTextfield").val());
  });
  //
  // Handle changing request ID selection
  // var req_id_select = document.getElementById("runNmbrTextfield");
  // req_id_select.addEventListener("change", function() {
  //   set_new_request_id($("#runNmbrTextfield").val());
  // });
  // Handle changing event type selection
  var event_type_select = document.getElementById("evtSelect");
  event_type_select.addEventListener("change", function () {
    var event_type = $("#evtSelect").val();
    // Clear current options
    $("#fileSelect").empty();
    // Populate with new options
    $.each(req_data[event_type], function (index, value) {
      $("#fileSelect").append(`<option>${value}</option>`);
    });
  });
});
