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
// import {Spinner} from "./external/spin-4.1.2/spin.min.js";

var logbook_data = {
  VELO: {
    MOptions: null,
    Options:
      "VELO",
    Level: null
  },
  MUON: {
    MOptions: null,
    Options:
      "MUON",
    Level: "Info, Warning, Severe",
  },
  "TestLogbook": {
    MOptions: "Test",
    Options: null,
    Level: null
  },
  "HLT": {
    MOptions:
      "HLT",
    Options: null,
    Level: null
  },
  Shift: {
    MOptions: null,
    Options:
      "LHCb, Velo, RICH1, UT, RICH2, RICH, SCIFI, CALO, ECAL, HCAL, MUON, PLUME, HLT1, HLT2, TFC, Magnet, LHC, DSS, Monitoring, Access, ONLINE, ALIGNMENT, CALIBRATION",
      Level: null
  },
  Online: {
    MOptions: null,
    Options: "DAQ",
    Level: null
  },
  "Data Quality": {
    MOptions:
      "Velo, PLUME, UT, RICH, CALO, MUON, HLT",
    Options: null,
    Level: null
  },
  RICH: {
    MOptions:
      "RICH, RICH1, RICH2",
    Options: null,
    Level: null
  },
  CALO: {
    MOptions: null,
    Options:
      "Calo, ECAL, HCAL",
    Level: null
  },
  "Alignment and calibration": {
    MOptions: null,
    Options:
      "RTA, Alignment, Calibration",
    Level: null
  },
  UT: {
    MOptions: null,
    Options:
      "UT",
    Level: null
  },
  SciFi: {
    MOptions: null,
    Options:
      "SciFi",
    Level: null
  },
  PLUME: {
    MOptions: null,
    Options:
      "PLUME",  
    Level: null
  },
  BCM: {
    MOptions: null,
    Options:
      "Flux Report, Piquet Report, BCM, Dump Report, SBCM Development",  
    Level: null
  }
};

var problemdb_subsystems = [
  "VELO", "UT", "RICH1", "SCIFI", "ECAL", "HCAL", "MUON", "ONLINE", "RTA-HLT1", "RTA-HTL2", "RTA-AC", "PLUME", "SMOG", "LUMI", "BEAM"
];

var subsys_template = `
<label>Subsystem</label>
<div class="row">
        <div class="col-xs-6 form-group">
                {{#subsystems_a}}
                    <div><input type="{{selection_type}}" name="subsystem" value="{{text}}" {{checked}}/> {{text}}</div>
                {{/subsystems_a}}
        </div>
        <div class="col-xs-6 form-group">
                {{#subsystems_b}}
                    <div><input type="{{selection_type}}" name="subsystem" value="{{text}} {{checked}}"/> {{text}}</div>
                {{/subsystems_b}}
        </div>
</div>
`;

var level_template = `
{{#title}}
<label>Severity Level</label>
<div class="row">
        <div class="col-xs-6 form-group">
                {{#levels}}
                    <div><input type="{{selection_type}}" name="level" value="{{text}}" {{checked}}/> {{text}}</div>
                {{/levels}}
        </div>
        <div class="col-xs-6 form-group">
        </div>
</div>
{{/title}}
`;

function unique(arr) {
  var u = {},
    a = [];
  for (var i = 0, l = arr.length; i < l; ++i) {
    if (!u.hasOwnProperty(arr[i])) {
      a.push(arr[i]);
      u[arr[i]] = 1;
    }
  }
  return a;
}

var save_refresh = true ;

export function show_elog_modal() {
  var is_online = window.location.href.indexOf("online_dq") !== -1;

  // Stop the refresh process first if in online mode
  if ( is_online ) {
    save_refresh = window._refresh_enabled ;
    window._refresh_enabled = false ;
  }

  $("#elog-modal").modal({
    backdrop: "static",
    keyboard: false
  });
  $("#elog-modal").draggable({
    handle: ".modal-header"
  });

  try {
    var run_number = $("#runNmbrTextfield").val();
    if (run_number == undefined) {
      run_number = 'unknown';
      $.ajax({
        type: "GET",
        cache: false,
        async: false,
        url: "/online_runnumber?mode=online&partition="+$("#partition-field").val(),
        success: function(server_reply) { 
          run_number = server_reply.run_number ;
          online_run_number = run_number ;
        }, 
        error: function(response) {
          run_number = 'unknown' ;
        }
      });
    }
    $("#elog-text").val("\n\n---------\nRun #" + run_number);
  } catch (err) {
    console.log(err);
  }
  $("#elog-modal").modal("show");
}

export function hide_elog_modal() {
  var current_logbook = $("#elog-logbook").val();

  $("#elog-text").val("");
  $("#elog-modal").modal("toggle");
  var is_online = window.location.href.indexOf("online_dq") !== -1;
  if ( is_online ) {
    window._refresh_enabled = save_refresh ;
  }
}

var elog_spinner;
function add_elog_spinner() {
  var opts = {
    lines: 13, // The number of lines to draw
    length: 10, // The length of each line
    width: 5, // The line thickness
    radius: 5, // The radius of the inner circle
    corners: 1, // Corner roundness (0..1)
    rotate: 0, // The rotation offset
    direction: 1, // 1: clockwise, -1: counterclockwise
    color: "#000", // #rgb or #rrggbb or array of colors
    speed: 1, // Rounds per second
    trail: 60, // Afterglow percentage
    shadow: false, // Whether to render a shadow
    hwaccel: false, // Whether to use hardware acceleration
    className: "spinner", // The CSS class to assign to the spinner
    zIndex: 2e9, // The z-index (defaults to 2000000000)
    top: "200px", // Top position relative to parent in px
    left: "auto" // Left position relative to parent in px
  };

  var target = document.getElementById("maincontainer");
  elog_spinner = new Spinner(opts).spin(target);
}

export function submit_to_elog() {
  if (elog_spinner) elog_spinner.stop();
  add_elog_spinner();

  var current_logbook = $("#elog-logbook").val();
  var checked_subsystems = get_selected_subsystems();
  var checked_level = get_selected_level();
  if (checked_level.length>0){  
    checked_level = checked_level[0] ;
  } else { 
    checked_level = '' ;
  }

  var problemdb_box = document.getElementById("problemdb-submit");
  var submit_to_problemdb = "no";
  if (problemdb_box) {
    submit_to_problemdb = problemdb_box.checked ? "yes" : "no";
  }
  var run_number = $("#runNmbrTextfield").val();
  if (run_number == undefined && typeof online_run_number !== "undefined") {
    run_number = online_run_number;
  }
  var payload = {
    logbook: $("#elog-logbook").val(),
    author: $("#elog-fullname").val(),
    subsystem: checked_subsystems.join(" | "),
    subject: $("#elog-subject").val(),
    run_number: run_number,
    level: checked_level,
    text: $("#elog-text").val(),
    images: [],
    submit_to_problemdb: submit_to_problemdb
  };

  if ( ! payload["subject"]) {
    alert("Subject is mandatory");
    elog_spinner.stop();
  } else {
    html2canvas(document.getElementById("main"),  {
      width: Math.max(document.getElementById("svg-canvas").scrollWidth,document.getElementById("pageheader").scrollWidth),
      height: document.getElementById("svg-canvas").scrollHeight+document.getElementById("pageheader").scrollHeight+60+document.getElementById("information-panel").offsetHeight,
      windowWidth: Math.max(document.getElementById("svg-canvas").scrollWidth+document.getElementById("pageheader").scrollWidth),
      windowHeight: document.getElementById("svg-canvas").scrollHeight+document.getElementById("pageheader").scrollHeight+60+document.getElementById("information-panel").offsetHeight,
      scrollX: -window.scrollX,
      scrollY: -window.scrollY
      }).then((canvas) => {
      payload["images"].push(canvas.toDataURL("image/png"));

      $.ajax({
        type: "POST",
        url: "elog_submit",
        data: JSON.stringify(payload),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function(data,statusText, jqXHR) {
          if (data.ok == true) {
            alert("Successfuly submitted!");
            elog_spinner.stop();
            hide_elog_modal(); 
          } else {
            alert("Error while submitting: `" +
            data.message +
            "`. Ping us on lhcb-monet@cern.ch");
            elog_spinner.stop();
         }
         elog_spinner.stop();
        },
        failure: function(jqXHR, textStatus, errorThrown) {
          alert("Problem sending to ELOG");
          elog_spinner.stop();
        }
      });
    });
  }
}

function get_logbook() {
  if (!$("#elog-logbook").length) return "";

  return $("#elog-logbook").val();
}

function get_default_logbook() {
  var is_online = window.location.href.indexOf("online_dq") !== -1;
  var is_history = window.location.href.indexOf("history_dq") !== -1;

  if (is_online || is_history) {
    return "Shift";
  } else {
    return "Data Quality";
  }
}

function elog_init() {
  if (get_logbook() == "") return;

  var select_field_html = "";
  var default_logbook = get_default_logbook();
  for (var logbook in logbook_data) {
    if (!logbook_data.hasOwnProperty(logbook)) continue;

    if (logbook != default_logbook)
      select_field_html += "<option>" + logbook + "</option>";
    else
      select_field_html +=
        '<option selected="selected">' + logbook + "</option>";
  }
  $("#elog-logbook").html(select_field_html);
  logbook_show_subsys();

  var select = document.getElementById("elog-logbook");
  select.addEventListener("change", function() {
    logbook_show_subsys();
  });
}

function get_selected_subsystems() {
  var boxes = document.getElementsByName("subsystem");
  var ret = [];

  for (var box of boxes) {
    if (box.checked) {
      ret.push(box.value);
    }
  }

  return ret;
}

function get_selected_level() {
  var boxes = document.getElementsByName("level");
  var ret = [];

  for (var box of boxes) {
    if (box.checked) {
      ret.push(box.value);
    }
  }

  return ret;
}

function logbook_show_subsys() {
  var current_logbook = $("#elog-logbook").val();
  var subsys_html = '<label for="elog-system">Subsystem</label><br/>';

  var multiple = true;
  var subsystems = logbook_data[current_logbook].MOptions;
  var has_levels = true;
  var list_levels = logbook_data[current_logbook].Level;

  if (subsystems == null) {
    multiple = false;
    subsystems = logbook_data[current_logbook].Options;
  }

  if (list_levels == null) {
    has_levels = false ;
  } else{
    list_levels = list_levels.split(",").map(function(s) {
      return s.trim();
    });
  }

  if (subsystems == null) {
    alert("Error loading subsystems!");
    return;
  }

  subsystems = subsystems.split(",").map(function(s) {
    return s.trim();
  });

  var left_part = [];
  var right_part = [];
  var is_notchecked_left_part = [] ;
  var is_notchecked_right_part = [] ;
  var is_checked_left_part = [] ;
  var is_checked_right_part = [] ;
  
  if (subsystems.length > 1) {
    var half_length = Math.ceil(subsystems.length / 2);
    var left_part = subsystems.splice(0, half_length);
    var right_part = subsystems;
  } else {
    left_part = subsystems;
  }

  left_part.forEach(function(item, index, array) {
    is_notchecked_left_part.push({'text': item, 'checked': ''});
    is_checked_left_part.push({'text': item, 'checked': ''});
  });

  right_part.forEach(function(item, index, array) {
    is_notchecked_right_part.push({'text': item, 'checked': ''});
    is_checked_right_part.push({'text': item, 'checked': ''});
  });

  if (subsystems.length>0) {
    is_checked_left_part[0] = {'text': is_checked_left_part[0]['text'], 'checked': 'checked'};
  }

  var output = mustache.render(subsys_template, {
    subsystems_a: multiple ? is_notchecked_left_part : is_checked_left_part,
    subsystems_b: multiple ? is_notchecked_right_part : is_checked_right_part,
    selection_type: multiple ? "checkbox" : "radio"
  });
  $("#subsys-checkboxes").html(output);
  
  var select = document.getElementById("subsys-checkboxes");
  select.addEventListener("change", function() {
    verify_subsystem_choice_is_compatible_with_problemdb();
  });

  var level_vector = [] ;

  if (has_levels) { 
    list_levels.forEach(function(item,index,array) { 
      level_vector.push({'text': item, 'checked': ''});
    });
    if ( list_levels.length>0) {
      level_vector[0] = { 'text': level_vector[0]['text'], 'checked': 'checked'} ;
    }
  }

  var output2 = mustache.render(level_template, {
    title: has_levels ? true : false,
    levels: level_vector,
    selection_type: "radio"
  });
  $("#level-checkboxes").html(output2);
}

function verify_subsystem_choice_is_compatible_with_problemdb() {
  var box = document.getElementById("problemdb-submit");
  if (!box) {
    return;
  }
  let checked_subsystems = get_selected_subsystems();
  var all_good = checked_subsystems.length != 0;
  for (var ix in checked_subsystems) {
    let subsystem = checked_subsystems[ix].trim();
    if (problemdb_subsystems.indexOf(subsystem) == -1) {
      all_good = false;
      break;
    }
  }

  $("#problemdb-submit").prop("disabled", !all_good);
  if (!all_good) {
    $("#problemdb-submit").prop("checked", false);
  }
}

$(function() {
  setTimeout(function() {
    mustache.parse(subsys_template);
  }, 0);

  elog_init();
});
