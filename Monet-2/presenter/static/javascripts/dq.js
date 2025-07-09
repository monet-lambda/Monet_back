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

window.last_dashboard_node_id = undefined;

// Disable buttons while loading
function disable_nav_bar(disabled) {
  var buttons = $(".btn-default").each(function() {
    if (disabled) {
      $(this).addClass("disabled");
    } else {
      $(this).removeClass("disabled");
    }
  });
}

function update_reference_glyph(state) {
  var glyphs = {
    activated: 'glyphicon-ok',
    deactivated: 'glyphicon-remove'
  }

  var icon = $('#changeReferenceModeIcon')
  icon.attr('class', 'glyphicon ' + glyphs[state])
}

function init_reference_state_button() {
  var button = $('#changeReferenceMode')

  var state = button.data('state')

  update_reference_glyph(state)
}

function change_reference_mode () {
  var button = $('#changeReferenceMode')
  var current_state = button.data('state')

  var new_state = {
    deactivated: 'activated',
    activated: 'deactivated'
  }[current_state]

  $.ajax({
    async: true,
    type: 'GET',
    url: 'change_reference_state',
    data: { state: new_state },

    success: function (json) {
      update_reference_glyph(new_state)
      button.data('state', new_state)

      if (window.last_dashboard_node_id)
        document
          .getElementById(window.last_dashboard_node_id + '_anchor')
          .click()
    },

    error: function (xhr, ajaxOptions, thrownError) {
      alert('/change_reference_state error:' + thrownError)
      set_status_field('', 'danger')
    }
  })
}


function set_status_field (message, status) {
  $('#statusForm').show()
  $('#statusIndicatorContainer').removeClass('btn-success')
  $('#statusIndicatorContainer').removeClass('btn-danger')
  $('#statusIndicatorContainer').removeClass('btn-info')
  $('#statusIndicatorContainer').removeClass('btn-warning')

  $('#statusIndicatorIcon').removeClass('glyphicon-ok')
  $('#statusIndicatorIcon').removeClass('glyphicon-exclamation-sign')
  $('#statusIndicatorIcon').removeClass('glyphicon-question-sign')

  if (status == 'warning') {
    $('#statusIndicatorContainer').addClass('btn-warning')
    $('#statusIndicatorIcon').addClass('glyphicon-exclamation-sign')
  } else if (status == 'danger') {
    $('#statusIndicatorContainer').addClass('btn-danger')
    $('#statusIndicatorIcon').addClass('glyphicon-exclamation-sign')
  } else if (status == 'info') {
    $('#statusIndicatorContainer').addClass('btn-info')
    $('#statusIndicatorIcon').addClass('glyphicon-exclamation-sign')
  } else if (status == 'success') {
    $('#statusIndicatorContainer').addClass('btn-success')
    $('#statusIndicatorIcon').addClass('glyphicon-ok')
  } else {
    alert('Unrecognised Status for status field!')
  }

  $('#statusIndicatorText').text(message)
}

export function compare_with_run( ) {
  let compare_run = prompt("Enter run number")
  if (compare_run==null) return

  if (window.last_dashboard_node_id) {
    load_dashboard(window.last_dashboard_node_id, undefined, compare_run, undefined);
  }
}

export function compare_with_fill( ) {
  let compare_fill = prompt("Enter fill number")
  if (compare_fill==null) return

  if (window.last_dashboard_node_id) {
    load_dashboard(window.last_dashboard_node_id, undefined, undefined, compare_fill);
  }
}