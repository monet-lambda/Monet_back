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
var date_format = 'MM/DD/YYYY HH:mm'

function decrease_run_number () {
  if ($('#runNmbrTextfield').val() == '') return

  if ($('#source-type-field').val() == 'Interval') {
    $('#interval-begin').data('DateTimePicker').date(get_diff_date(false))
    set_new_run_number(parseInt($('#runNmbrTextfield').val()))
    return
  }

  var runnumber = parseInt($('#runNmbrTextfield').val())
  $.ajax({
    async: true,
    type: 'GET',
    url: 'get_previous_runnumber?runnumber=' + runnumber,

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

function increase_run_number (latest) {
  var url = ''
  if (latest) {
    url = 'get_latest_runnumber'
  } else {
    var runnumber = parseInt($('#runNmbrTextfield').val())
    url = 'get_next_runnumber?runnumber=' + runnumber
    if ($('#runNmbrTextfield').val() == '') return
  }

  if ($('#source-type-field').val() == 'Interval') {
    if (latest) {
      $('#interval-begin').data('DateTimePicker').maxDate(false)
      $('#interval-begin').data('DateTimePicker').date(moment())
      $('#interval-begin').data('DateTimePicker').date(get_diff_date(false))
    } else {
      $('#interval-begin').data('DateTimePicker').date(get_diff_date(true))
    }
    set_new_run_number(0)
    return
  }

  $.ajax({
    async: true,
    type: 'GET',
    url: url,

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

function get_diff_date (add) {
  begin_date = $('#interval-begin').data('DateTimePicker').date()
  diff_hours = $('#interval-size').data('DateTimePicker').date().hours()
  diff_minutes = $('#interval-size').data('DateTimePicker').date().minutes()
  if (add) {
    return begin_date.add(diff_hours, 'hours').add(diff_minutes, 'minutes')
  } else {
    return begin_date
      .subtract(diff_hours, 'hours')
      .subtract(diff_minutes, 'minutes')
  }
}

function set_new_run_number (run_number) {
  var url = 'browse_run?'
  url += 'run_number=' + run_number
  url += '&reference_state=' + $('#changeReferenceMode').data('state')
  url += '&selected_page=' + $('.jstree-container-ul').jstree('get_selected')[0]
  url += '&partition=' + $('#partition-field').val()

  if ($('#source-type-field').val() == 'Interval') {
    url +=
      '&interval_begin=' +
      $('#interval-begin').data('DateTimePicker').date().format(date_format)
    url +=
      '&interval_size=' +
      $('#interval-size').data('DateTimePicker').date().format('HH:mm')
    url += '&data_source=' + 'history_interval'
  }
  window.location.href = url
}

function set_run_to_ui_value () {
  set_new_run_number($('#runNmbrTextfield').val())
}

$(function () {
  init_reference_state_button()

  $('#changeReferenceMode').click(function () {
    change_reference_mode()
  })

  var select = document.getElementById('partition-field')
  select.addEventListener('change', function () {
    set_run_to_ui_value()
  })

  $('#setRunNmbrButton').click(function () {
    set_run_to_ui_value()
  })

  $('#runNmbrTextfield').keypress(function (e) {
    if (e.keyCode == 13) {
      set_run_to_ui_value()
    }
  })
  $('#decreaseRunNmbrButton').click(function () {
    decrease_run_number()
  })
  $('#increaseRunNmbrButton').click(function () {
    increase_run_number(false)
  })
  $('#increaseUncheckedRunNmbrButton').click(function () {
    increase_run_number(true)
  })
})

function set_rundb_info () {
  var run_number = $('#runNmbrTextfield').val()
  var fill_number = -1
  if ($('#source-type-field').val() == 'Fill') {
    fill_number = run_number
    run_number = -1
  }
  $.ajax({
    async: true,
    type: 'GET',
    url: '/rundb',
    data: { run: run_number, fill: fill_number },

    success: function (server_reply) {
      if (!server_reply.success) return

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
  })
}

$(document).ready(function () {
  var begin_date
  var interval_size
  if ($('#interval-begin').val()) {
    begin_date = moment($('#interval-begin').val(), date_format)
  } else {
    begin_date = moment().subtract(30, 'minutes')
  }
  if ($('#interval-size').val() && $('#interval-size').val() != 'None') {
    interval_size = $('#interval-size').val()
  } else {
    interval_size = '00:30'
  }

  $('#interval-begin').datetimepicker({
    maxDate: moment(),
    format: 'Fro\\m ' + date_format,
    sideBySide: true,
    useStrict: true,
    date: begin_date
  })

  $('#interval-size').datetimepicker({
    format: 'for H:mm',
    date: moment(interval_size, 'HH:mm')
  })

  if ($('#source-type-field').val() == 'Interval') { 
    $('#partition-field').show()
  } else {
    $('#partition-field').hide()
  }

  $('#source-type-field').change(function () {
    Cookies.set('source-type-field', $(this).val(), { sameSite: 'Lax' })
    if ($(this).val() == 'Interval') {
      $('.history_interval').show()
      $('#runNmbrTextfield').hide()
      $('#partition-field').show()
      $('#runInfo').hide()
    } else if ($(this).val() == 'Fill') {
      $('.history_interval').hide()
      $('#runNmbrTextfield').show()
      $('#partition-field').hide()
      var ri = $('#runInfo')
      ri[0].innerHTML =
        '<span class="glyphicon glyphicon-info-sign"></span><span>Fill Information</span>'
      ri[0].title = '<b>Fill Information</b>'
      $('#runInfo').show()
    } else {
      $('.history_interval').hide()
      $('#runNmbrTextfield').show()
      $('#partition-field').hide()
      var ri = $('#runInfo')
      ri[0].innerHTML =
        '<span class="glyphicon glyphicon-info-sign"></span><span>Run Information</span>'
      ri[0].title = '<b>Run Information</b>'
      $('#runInfo').show()
    }
  })

  var current_type = Cookies.get('source-type-field')
  if (current_type) {
    $('#source-type-field').val(current_type).trigger('change')
  }

  set_rundb_info()
})

