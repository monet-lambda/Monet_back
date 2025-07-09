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
var previousRunNumber = 0

export function show_flag_modal () {
  var run_number = $('#runNmbrTextfield').val()
  $.ajax({
    async: true,
    type: 'GET',
    url: '/rundb',
    data: { runnumber: run_number },

    success: function (json) {
      set_run_flag(
        json.run_flag,
        json.run_system_flags.SMOG2,
        json.run_system_flags.PLUME,
        json.run_system_flags.UT
      )
    }
  })

  $('#flag-modal').modal({
    backdrop: 'static',
    keyboard: false
  })
  $('#flag-select-modal').show()
  $('#flag-progress-modal').hide()

  $('#flag-modal').modal('show')
}

function get_range () {
  var run_start = parseInt($('#flag_range_from').val())
  var run_end = parseInt($('#flag_range_to').val())

  var success = true
  if (isNaN(run_start)) {
    success = false
    alert('Start run not specified')
  } else {
    if (isNaN(run_end)) {
      success = false
      alert('End run not specified')
    }
  }

  if (run_start > run_end) {
    success = false
    alert('End run smaller than start run')
  }

  return {
    run_start: run_start,
    run_end: run_end,
    success: success
  }
}

export function flag_range_all_ok () {
  const { run_start, run_end, success } = get_range()
  if (!success) return

  if (
    !confirm(
      'Are you sure you want to flag runs from ' +
        run_start +
        ' to ' +
        run_end +
        ' all OK'
    )
  )
    return

  let elog_message = prompt( "Enter ELOG message" )
  if (elog_message == null ) 
    return

  $.ajax({
    async: true,
    type: 'GET',
    url: '/flag_run_range',
    data: { run_start: run_start, run_end: run_end, flag: 'OK', elog_message: elog_message },

    success: function (json) {
      if (!json['success']) {
        alert('Problem flagging the run range')
      } else {
        alert('Runs flagged OK')
      }
    },
    error: function (json) {
      alert('Error flagging runs')
    }
  })
}

export function flag_range_all_bad () {
  const { run_start, run_end, success } = get_range()
  if (!success) return

  if (
    !confirm(
      'Are you sure you want to flag runs from ' +
        run_start +
        ' to ' +
        run_end +
        ' all BAD'
    )
  )
    return

  let elog_message = prompt( "Enter ELOG message" )
  if (elog_message == null ) 
    return  

  $.ajax({
    async: true,
    type: 'GET',
    url: '/flag_run_range',
    data: { run_start: run_start, run_end: run_end, flag: 'BAD', elog_message: elog_message },

    success: function (json) {
      if (!json['success']) {
        alert('Problem flagging the run range')
      } else {
        alert('Runs flagged BAD')
      }
    },
    error: function (json) {
      alert('Error flagging runs')
    }
  })
}

export function flag_range_all_conditional () {
  const { run_start, run_end, success } = get_range()
  if (!success) return

  if (
    !confirm(
      'Are you sure you want to flag runs from ' +
        run_start +
        ' to ' +
        run_end +
        ' all CONDITIONAL'
    )
  )
    return

  let elog_message = prompt( "Enter ELOG message" )
  if (elog_message == null ) 
    return
  
  $.ajax({
    async: true,
    type: 'GET',
    url: '/flag_run_range',
    data: { run_start: run_start, run_end: run_end, flag: 'CONDITIONAL', elog_message: elog_message },

    success: function (json) {
      if (!json['success']) {
        alert('Problem flagging the run range')
      } else {
        alert('Runs flagged CONDITIONAL')
      }
    },
    error: function (json) {
      alert('Error flagging runs')
    }
  })
}

export function flag_range_all_smog2ok () {
  const { run_start, run_end, success } = get_range()
  if (!success) return

  if (
    !confirm(
      'Are you sure you want to flag runs from ' +
        run_start +
        ' to ' +
        run_end +
        ' all SMOG2 OK'
    )
  )
    return

  $.ajax({
    async: true,
    type: 'GET',
    url: '/flag_extra_run_range',
    data: { run_start: run_start, run_end: run_end, extra_flag: 'SMOG2' },

    success: function (json) {
      if (!json['success']) {
        alert('Problem flagging the run range')
      } else {
        alert('Runs flagged CONDITIONAL')
      }
    },
    error: function (json) {
      alert('Error flagging runs')
    }
  })
}

export function flag_range_fill_table () {
  const { run_start, run_end, success } = get_range()
  if (!success) return

  $.ajax({
    async: true,
    type: 'GET',
    url: '/rundb_range',
    data: { run_start: run_start, run_end: run_end },

    success: function (json) {
      if (!json['success']) {
        alert('No run found in this range')
      } else {
        var tabledata = []
        json.rundb_info.forEach(element => {
          tabledata.push({
            runnumber: element['runid'],
            partition: element['partitionname'],
            dqflagbkk: element['flag_bkk'],
            dqflagbkk_extra: element['flag_bkk_extra'],
            dqflagdqdb: element['flag_dqdb'],
            dqflagdqdb_extra: element['flag_dqdb_extra']
          })
        })

        var table = Tabulator.findTable('#flag_range_table')[0]
        table.replaceData(tabledata)
      }
    }
  })
}

export function show_range_flag_modal () {
  var run_number = $('#runNmbrTextfield').val()

  $('#flag-range-modal').modal({
    backdrop: 'static',
    keyboard: false
  })

  var table = new Tabulator('#flag_range_table', {
    height: '100%',
    layout: 'fitColumns', //fit columns to width of table (optional)
    columns: [
      //Define Table Columns
      { title: 'Run number', field: 'runnumber' },
      { title: 'Partition', field: 'partition' },
      { title: 'DQ flag in Dirac', field: 'dqflagbkk' },
      { title: 'Extra flags in Dirac', field: 'dqflagbkk_extra' },
      { title: 'DQ flag in DQDB', field: 'dqflagdqdb' },
      { title: 'Extra flags in DQDB', field: 'dqflagdqdb_extra' }
    ]
  })

  $('#flag-range-modal').modal('show')
}

export function update_reference_function (run_number) {
  var run_number = $('#runNmbrTextfield').val()
  // Show confirmation dialog
  const confirmation = confirm(
    'Are you sure you want to update the reference for this run number:  ' +
      run_number +
      '?'
  )
  if (confirmation) {
    $.ajax({
      async: true,
      type: 'GET',
      url: '/update_reference',
      data: { runnumber: run_number },

      success: function () {
        alert('Reference updated for run ' + run_number)
        // Simulate UI change to indicate the reference has been updated
        const updateLabel = document.getElementById('update_reference_label')
        if (!updateLabel) {
          // Create label if it doesn't exist
          const newLabel = document.createElement('span')
          newLabel.id = 'update_reference_label'
          newLabel.innerHTML = '<br><strong>Reference updated</strong>'
          document.querySelector('.navbar-left').appendChild(newLabel)
        } else {
          // Update existing label
          updateLabel.innerHTML = 'Reference updated for run ' + run_number
        }
      }
    })
  }
}


function decrease_run_number (unchecked_only, migrated_only) {
  if ($('#runNmbrTextfield').val() == '') return
  var runnumber = parseInt($('#runNmbrTextfield').val())
  $.ajax({
    async: true,
    type: 'GET',
    url:
      'get_previous_runnumber?runnumber=' +
      runnumber +
      '&unchecked_only=' +
      unchecked_only +
      '&migrated_only=' +
      migrated_only,

    success: function (json) {
      if (!json.success) {
        alert(json.data.message)
        return
      }
      set_new_run_number(json['data']['runnumber'])
    },

    error: function (xhr, ajaxOptions, thrownError) {
      alert('Run switch error:' + thrownError)
      set_status_field('JSON Error:' + thrownError, 'danger')
    },
    complete: function () {
      disable_nav_bar(false)
    }
  })
}

function increase_run_number (unchecked_only, migrated_only) {
  if ($('#runNmbrTextfield').val() == '') return
  var runnumber = parseInt($('#runNmbrTextfield').val())
  $.ajax({
    async: true,
    type: 'GET',
    url:
      'get_next_runnumber?runnumber=' +
      runnumber +
      '&unchecked_only=' +
      unchecked_only +
      '&migrated_only=' +
      migrated_only,

    success: function (json) {
      if (!json.success) {
        alert(json.data.message)
        return
      }
      set_new_run_number(json['data']['runnumber'])
    },

    error: function (xhr, ajaxOptions, thrownError) {
      alert('Run switch error:' + thrownError)
      set_status_field('JSON Error:' + thrownError, 'danger')
    },
    complete: function () {
      disable_nav_bar(false)
    }
  })
}

function set_run_number_visual_feedback (server_reply, run_number) {
  if (server_reply.success) {
    if ($('#runInfo').length > 0) {
      var popover = $('#runInfo').data('bs.popover')
      popover.options.html = true
      popover.options.sanitize = false
      popover.options.content = server_reply.rundb_info

      var popover_is_visible = $('#runInfo')
        .data('bs.popover')
        .tip()
        .hasClass('in')
      if (popover_is_visible) {
        $('#runInfo').popover('show')
      }
    }
  } else {
    set_status_field('', 'danger')
    alert(
      `
Hi,
Seems like something failed in Monet backend while setting run number.
Please contact us on lhcb-monet@cern.ch
Technical information below:\n\n
Run number: ` +
        run_number +
        '\n' +
        JSON.stringify(server_reply)
    )
  }
}

function set_new_run_number (run_number) {
  // Check if run is migrated offline
  var cont = true
  $.ajax({
    async: false,
    timeout: 3000,
    type: 'GET',
    url: '/rundb_json',
    data: { run: run_number },

    success: function (server_reply) {
      if (!server_reply.success) {
        alert('Run database server did not answer')
        return
      }
      if (
        server_reply.rundb_info.destination != 'OFFLINE' ||
        server_reply.rundb_info.state != 'MIGRATED'
      ) {
        alert(
          'This run is not in state MIGRATED OFFLINE ! Stay on the current one.'
        )
        cont = false
      }
    }
  })

  if (!cont) {
    run_number = previousRunNumber
  }
  previousRunNumber = run_number

  var url = 'browse_run?'
  url += 'run_number=' + run_number
  url += '&procpass=' + get_procpass()
  url += '&reference_state=' + $('#changeReferenceMode').data('state')
  url += '&selected_page=' + $('.jstree-container-ul').jstree('get_selected')[0]

  window.location.href = url
}

export function set_run_flag (
  run_flag,
  run_smog_tag = '',
  run_plume_tag = '',
  run_ut_tag = ''
) {
  $('#run-tag').val(String(run_flag))
  var sel = $('#run-tag')
  sel.data('prev', String(run_flag))
  $('#run-smog-tag').val(String(run_smog_tag))
  var sel_smog = $('#run-smog-tag')
  sel_smog.data('prev', String(run_smog_tag))
  $('#run-plume-tag').val(String(run_plume_tag))
  var sel_plume = $('#run-plume-tag')
  sel_plume.data('prev', String(run_plume_tag))
  $('#run-ut-tag').val(String(run_ut_tag))
  var sel_ut = $('#run-ut-tag')
  sel_ut.data('prev', String(run_ut_tag))
}

function set_run_number () {
  // page_cache = {};
  $('#runNmbrTextfieldIndicatorContainer').addClass('hidden')
  var run_number = $('#runNmbrTextfield').val()
  disable_nav_bar(false)
  if (run_number == '0') return

  var procpass = ''
  if ($('#proc-pass-field').length) {
    // check if processing pass field exists
    procpass = $('#proc-pass-field').val()
  }

  $.ajax({
    async: true,
    type: 'GET',
    url: '/rundb',
    data: { runnumber: run_number },

    success: function (json) {
      set_run_number_visual_feedback(json, run_number)
      set_run_flag(
        json.run_flag,
        json.run_system_flags.SMOG2,
        json.run_system_flags.PLUME,
        json.run_system_flags.UT
      )

      if (window.last_dashboard_node_id)
        document
          .getElementById(window.last_dashboard_node_id + '_anchor')
          .click()
    },

    error: function (xhr, ajaxOptions, thrownError) {
      alert('/set_run_number error:' + thrownError)
      set_status_field('', 'danger')
    },

    complete: function () {
      disable_nav_bar(false)
    }
  })
}

function init_run_number_icon () {
  var passed_run_number = unescape(getUrlParameter('run_number'))
  if (passed_run_number != 'undefined')
    $('#runNmbrTextfield').val(passed_run_number)

  if ($('#runNmbrTextfield').val() != '') {
    set_run_number()
  }
}

function get_procpass () {
  if (!$('#proc-pass-field').length) return ''

  return $('#proc-pass-field').val()
}

function set_rundb_info () {
  var run_number = $('#runNmbrTextfield').val()

  $.ajax({
    async: true,
    type: 'GET',
    url: '/rundb',
    data: { run: run_number },

    success: function (server_reply) {
      if (!server_reply.success) return
      if ($('#runInfo').length > 0) {
        var popover = $('#runInfo').data('bs.popover')
        popover.options.html = true
        popover.options.sanitize = false
        popover.options.content = server_reply.rundb_info

        var popover_is_visible = $('#runInfo')
          .data('bs.popover')
          .tip()
          .hasClass('in')
        if (popover_is_visible) {
          $('#runInfo').popover('show')
        }
      }
    }
  })
}

$(document).ready(function () {
  init_reference_state_button()
  init_run_number_icon()
  previousRunNumber = $('#runNmbrTextfield').val()
  $('#runNmbrTextfield').keypress(function (e) {
    if (e.keyCode == 13) {
      set_new_run_number($('#runNmbrTextfield').val())
      return false
    }
  })
  $('#changeReferenceMode').click(function () {
    change_reference_mode()
  })
  $('#setRunNmbrButton').click(function () {
    set_new_run_number($('#runNmbrTextfield').val())
  })
  $('#decreaseRunNmbrButton').click(function () {
    decrease_run_number(false, false)
  })

  $('#decreaseUncheckedRunNmbrButton').click(function () {
    decrease_run_number(true, true)
  })
  $('#increaseUncheckedRunNmbrButton').click(function () {
    increase_run_number(true, true)
  })

  $('#decreaseMigratedRunNmbrButton').click(function () {
    decrease_run_number(false, true)
  })
  $('#increaseMigratedRunNmbrButton').click(function () {
    increase_run_number(false, true)
  })

  var sel = $('#run-tag')
  sel.data('prev', sel.val())
  sel.change(function (data) {
    var jqThis = $(this)
    if (jqThis.data('prev') === 'UNCHECKED') {
      return
    } else {
      if (
        confirm(
          'You are going to modify the flag of a run which is already flagged. Please confirm.'
        )
      ) {
        return
      } else {
        jqThis.val(jqThis.data('prev'))
      }
    }
  })

  var sel_smog = $('#run-smog-tag')
  sel_smog.data('prev', sel_smog.val())
  sel_smog.change(function (data) {
    var jqThis = $(this)
    if ($('#run-tag').data('prev') === 'UNCHECKED') {
      return
    } else {
      alert('Changing extra flags of a run already flagged is not possible.')
      jqThis.val(jqThis.data('prev'))
    }
  })

  var sel_plume = $('#run-plume-tag')
  sel_plume.data('prev', sel_plume.val())
  sel_plume.change(function (data) {
    var jqThis = $(this)
    if ($('#run-tag').data('prev') === 'UNCHECKED') {
      return
    } else {
      alert('Changing extra flags of a run already flagged is not possible.')
      jqThis.val(jqThis.data('prev'))
    }
  })

  var sel_ut = $('#run-ut-tag')
  sel_ut.data('prev', sel_ut.val())
  sel_ut.change(function (data) {
    var jqThis = $(this)
    if ($('#run-tag').data('prev') === 'UNCHECKED') {
      return
    } else {
      alert('Changing extra flags of a run already flagged is not possible.')
      jqThis.val(jqThis.data('prev'))
    }
  })

  set_rundb_info()

  if (get_procpass() == '') return

  var select = document.getElementById('proc-pass-field')
  select.addEventListener('change', function () {
    set_new_run_number($('#runNmbrTextfield').val())
  })
})

function add_spinner() {
  var opts = {
    lines: 13, // The number of lines to draw
    length: 20, // The length of each line
    width: 10, // The line thickness
    radius: 30, // The radius of the inner circle
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
    top: "15%", // Top position relative to parent in px
    left: "50%" // Left position relative to parent in px
  };

  var target = document.getElementById("flag-spinner");
  var spinner = new Spinner(opts).spin(target);
}

function indicate_flagging_complete(header, monet_reply) {
  $("#flag-progress-label").html(header);
  $("#flag-spinner").hide();
  $("#flag-progress-modal-body").html("");
  $("#flag-progress-modal-body").append(
    "Flagging complete: <br/> <pre>" +
      monet_reply["explanation"] +
      "</pre></br>"
  );
  $("#flag-progress-modal-body").append(
    "Full backend response: <br/> <pre>" +
      JSON.stringify(monet_reply) +
      "</pre>"
  );
  $("#flag-complete-btn").show();
}

function show_flag_progress_modal() {
  $("#flag-progress-label").html("Flagging in progress...");
  $("#flag-progress-modal-body").html(
    '<div style="height:200px"><span id="flag-spinner" style="position: absolute;display: block;top: 50%;left: 50%;"></span></div>'
  );
  add_spinner();
  $("#flag-complete-btn").hide();

  $("#flag-select-modal").hide();
  $("#flag-progress-modal").show();
}

function save_run_flag() {
  var number = $("#runNmbrTextfield").val();
  var flag = $("#run-tag").val();
  var smog_flag = $("#run-smog-tag").val();

  var elog_comment = $("#flag-elog-comment").val();
  if (flag == "BAD") {
    elog_comment +=
      "\n\n\n--------\n<MonetProblematicPages>\n" +
      $("#flag-problematic-pages").val() +
      "\n</MonetProblematicPages>";
  }

  if (((flag == "UNCHECKED") || (flag == "BAD")) && ((smog_flag == "OK"))) {
    indicate_flagging_complete(
      "&#10004; Flagging aborted!",
      { "explanation": "The extra DQ flag cannot be set if the run is not OK or CONDITIONAL" }
    );
    return ;
  }

  $.ajax({
    async: true,
    type: "POST",
    url: "save_run_flag",
    timeout: 3600000,
    data: {
      run_number: number,
      flag: flag,
      elog_comment: elog_comment,
      smog_flag: smog_flag,
    },

    success: function(server_response) {
      if (flag == server_response.saved_flag) {
        document.querySelector("#dqFlag").textContent = String(flag);
        indicate_flagging_complete(
          "&#10004; Successfuly flagged!",
          server_response
        );
      } else {
        indicate_flagging_complete(
          "<span style='color: #F00'> &#10008; Flag failed!</span>",
          server_response
        );
      }
    },

    error: function(xhr, ajaxOptions, thrownError) {
      indicate_flagging_complete("Flag failed!", thrownError);
    },

    complete: function() {
      var sel = $("#run-tag");
      sel.data("prev",flag);
      var sel_smog = $("#run-smog-tag");
      sel_smog.data("prev",smog_flag);
      disable_nav_bar(false);
    }
  });
}


export function submit_flag() {
  show_flag_progress_modal();
  save_run_flag();
}

export function hide_flag_range_modal() {
  var table = Tabulator.findTable("#flag_range_table")[0];
  table.destroy();
  $("#flag-range-modal").modal("toggle");
}

export function hide_flag_modal() {
  $("#flag-modal").modal("toggle");
}

function toggle_problematic_pages() {
  var flag = $("#run-tag").val();

  if ((flag == "BAD") || (flag == "CONDITIONAL")) {
    $("#problematic-pages-div").show();
  } else {
    $("#problematic-pages-div").hide();
  }
}

$(function() {
  if (!$("#run-tag").length) return;
  toggle_problematic_pages();

  var select = document.getElementById("run-tag");
  select.addEventListener("change", function() {
    toggle_problematic_pages();
  });
});
