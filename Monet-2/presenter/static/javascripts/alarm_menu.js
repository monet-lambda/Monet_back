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

function is_alarm_folder (node_id) {
  if (node_id) return node_id.indexOf('alarm-subsys-folder') == 0
}

function selectAlarmNode (e, data) {
  if (!is_alarm_folder(data.node.id))
    load_dashboard(data.node.original.histo_id, data.node.original.msg_id,undefined, undefined)
}

function createAlarmJSTrees (jsonData) {
  $('#alarmTree').jstree({
    core: {
      animation: 1,
      data: jsonData.alarms
    }
  })

  // $("#alarmTree").bind("open_node.jstree", function(event, data) {
  //     openNode(event, data)
  // });
  // $("#alarmTree").bind("close_node.jstree", function(event, data) {
  //     closeNode(event, data)
  // });
  $('#alarmTree').bind('select_node.jstree', function (event, data) {
    selectAlarmNode(event, data)
  })

  // $("#alarmTree").bind("loaded.jstree", function(event, data) {
  //     $("#reloadTreeButton").click(function() {
  //         reloadTree()
  //     });
  //     $("#openAllTreeButton").click(function() {
  //         openAllTree()
  //     });
  //     $("#closeAllTreeButton").click(function() {
  //         closeAllTree()
  //     });
  // });
}

function load_alarms () {
  $.ajax({
    async: true,
    type: 'GET',
    url: '/alarms',
    dataType: 'json',
    success: function (json) {
      createAlarmJSTrees(json)
      $('#loadingAlarms').css('display', 'none')
    },
    error: function (xhr, ajaxOptions, thrownError) {
      // alert("Alarm loading error:" + thrownError);
    }
  })
}

$(function () {
  load_alarms()
  // setInterval(load_alarms, 10000);
})
