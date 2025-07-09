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
export function getUrlParameter(sParam) {
  var sPageURL = decodeURIComponent(window.location.search.substring(1)),
    sURLVariables = sPageURL.split("&"),
    sParameterName,
    i;

  for (i = 0; i < sURLVariables.length; i++) {
    sParameterName = sURLVariables[i].split("=");

    if (sParameterName[0] === sParam) {
      return sParameterName[1] === undefined ? true : sParameterName[1];
    }
  }
};

var readFromDB = false;
var data_source = "offline";

var div_template = `<div style="position: absolute; left: {{cx}}px; top: {{cy}}px; width: {{sx}}px; height: {{sy}}px;">{{{div}}}</div>`;
var page_template = `
<div class="page-header" id="pageheader">
    <h2 style="display: inline"><span id="histopage-path">{{path}}</span></h2>

    <div id="pagedocs" class="btn-group btn-group-right" data-html2canvas-ignore>
       <div class="btn-group">
        <div class="btn-group">
            <div class="dropdown">
              <button class="btn btn-default dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
                Save
                <span class="caret"></span>
              </button>
              <ul class="dropdown-menu" aria-labelledby="dropdownMenu1">
                <li><a href="#" onclick="saveAllHistograms();">All plots</a></li>
                <li><a href="#" onclick="saveAllHistogramsAsSingleFile();">Whole page</a></li>
              </ul>
            </div>
        </div>
      </div>
    </div>

</div>

<div id="svg-canvas">
    {{#divs}}{{{resized_div}}}{{/divs}}
</div>

<div class="panel panel-default information-panel" id="information-panel" data-html2canvas-ignore>
    <div class="panel-heading">
        <h3 class="panel-title">
            <a id="collapsed_click" data-toggle="collapse" href="#collapsed_page_info" class="collapsed">
                Page Information
            </a>
        </h3>
    </div>
    <div id="collapsed_page_info" class="panel-collapse collapsed collapse">
        <div class="panel-body">
            <p>
                {{{pagedoc}}}
            </p>
        </div>
    </div>
</div>

<script>
// Collapse page info block
if (Cookies.get('collapsed_page_info_action') == "show") {
    $( "#collapsed_page_info" ).collapse("show");
}

$( "#collapsed_click" ).click(function() {
    $collapsed_page_info_action = Cookies.get('collapsed_page_info_action');

    if($collapsed_page_info_action == "hide") {
        $collapsed_page_info_action = "show";
    } else {
        $collapsed_page_info_action = "hide";
    }
    Cookies.set('collapsed_page_info_action', $collapsed_page_info_action, { sameSite: 'Lax' });
});

// Hack for smooth hiding
$('#information-panel').on('hide.bs.collapse', function (){
    $("#svg-canvas").css("bottom", 0);
});

// Hack for scrolling
$('#information-panel').on('shown.bs.collapse hidden.bs.collapse', function (){
    $("#svg-canvas").css("bottom", $("#information-panel").height());
});
</script>
<script>
    $('[data-toggle="popover"]').popover({
        html:true,
        container: "body"
    });
</script>`;


var page_template_for_doc = `
<div class="page-header" id="pageheader">
    <h2 style="display: inline"><span id="histopage-path">{{path}}</span></h2>

    <div id="pagedocs" class="btn-group btn-group-right" data-html2canvas-ignore>
       <div class="btn-group">
        <div class="btn-group">
            <div class="dropdown">
              <button class="btn btn-default dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
                Save
                <span class="caret"></span>
              </button>
              <ul class="dropdown-menu" aria-labelledby="dropdownMenu1">
                <li><a href="#" onclick="clickHandler();">As file</a></li>
              </ul>
            </div>
        </div>
      </div>
    </div>
</div>
<div id="svg-canvas">
    {{#divs}}{{{resized_div}}}{{/divs}}
</div>
`

var pagedoc_template = `
<div class="panel-body">
            <p>
                {{{pagedoc}}}
                <hr><p> <b>Descriptions for histograms:</b>
                <ul>
                <div id="description-list"></div>
                </ul>
                </p>
            </p>
        </div>
`

var pagedoc_template_for_doc = `
<div class="panel-body">
            <p>
                {{{pagedoc}}}
            </p>
        </div>
`

var error_template = `
<div id="svg-canvas">
<h4>Error while loading page</h4>
    <pre>{{error}}</pre>
</div>
`;

export function page_init() {
  setTimeout(function() {
    mustache.parse(div_template);
    mustache.parse(page_template);
    mustache.parse(error_template);
    mustache.parse(pagedoc_template);
  }, 0);
}
// Menu Tree
// Parameter "enforceReadFromDBFlag" is set to true, when user manually updates tree
// otherwise, data ist read from file
// Parameter "allNodesStandardState" is considered, when reading from DB. When
// allNodesStandardState == "opened" all nodes are opened
// allNodesStandardState == "closed" all nodes are closed
function treeAjaxCall(
  enforceReadFromDBFlag,
  allNodesStandardState,
  filterFlag,
  filter
) {
  //if both or any of the both flags is true => read from db
  readFromDB = enforceReadFromDBFlag || window.pageNormallyReadFromDBFlag;

  var menutree_json = localStorage.getItem("menutree_json");

  if (menutree_json != "undefined" && menutree_json) {
    createJSTrees(JSON.parse(menutree_json));
  }

  $.ajax({
    async: true,
    type: "GET",
    url: "menutree",
    dataType: "json",
    data: {
      loadFromDBFlag: readFromDB,
      allNodesStandardState: allNodesStandardState,
      filterFlag: filterFlag,
      filter: filter,
      menutree_timestamp: localStorage.getItem("menutree_timestamp")
    },
    success: function(json) {
      if (!json["current_actual"]) {
        createJSTrees(json["menutree_json"]);
        localStorage.setItem(
          "menutree_json",
          JSON.stringify(json["menutree_json"])
        );
        localStorage.setItem("menutree_timestamp", json["menutree_timestamp"]);
      }
    },
    error: function(xhr, ajaxOptions, thrownError) {
      alert("Tree menu loading error:" + thrownError);
    }
  });
}

//given HistoDB tree node ID (name), returns whether such node is a folder (i.e. not a leaf)
function is_folder_by_id(id) {
  //Folder Id start not with //F//

  return String(id).indexOf("//F//") == 0;
}

var spinner = null ;
var spinners = new Array(30); 

var small_spinner_opts = {
  lines: 13, // The number of lines to draw
  length: 20, // The length of each line
  width: 10, // The line thickness
  radius: 10, // The radius of the inner circle
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

function load_histograms( hist_dict , req , key_dict , number_dict ) {
  for (const [key, value] of Object.entries(hist_dict)) {
    req['histos_contained'] = "[" + value + "]";
    req['key_list'] = "[" + key_dict[key] + "]";
    req['histo_number']= number_dict[key];
    var target = document.getElementById( "maincontainer" ) ;
    spinners[ number_dict[key] ] = new Spinner(small_spinner_opts).spin( target );

    $.ajax({
      async: true,
      timeout: 150000,
      tryCount: 0,
      retryLimit: 0,  // PR, 27/04   set to 0 for the time being
      type: "POST",
      url: "single_histo",
      data: req,
    })
    .done(function(monet_data){
      var h_cx = monet_data.divs[0].size[0];
      var h_cy = monet_data.divs[0].size[1];
      var h_sx = monet_data.divs[0].size[2];
      var h_sy = monet_data.divs[0].size[3];

      var canvas_height = 0.85 * $("#sidebar").height();
      var canvas_width = $(window).width() - $("#sidebar").width();

      var base_height = Math.max(canvas_height, 300);
      var base_width = Math.max(canvas_width, 800);

      var div_params = {
        cx: Math.floor(base_width * h_cx),
        cy: Math.floor(base_height * (1.0 - h_sy) + 20),
        sx: Math.floor(0.95 * base_width * (h_sx - h_cx)),
        sy: Math.floor(0.95 * base_height * (h_sy - h_cy)),
        div: monet_data.divs[0].code,
      };
      var div_name = "#histo"+monet_data['histo_number'];
      var output = mustache.render( div_template, div_params );
      $(div_name).html(output);

      var div_description_name = "#histo-description"+monet_data['histo_number'];
      $(div_description_name).html(monet_data['pagedoc']);
      const fn = new Function( monet_data.script );
      fn(); 

      if ( spinners[parseInt(monet_data['histo_number'])] ) {
        spinners[parseInt(monet_data['histo_number'])].stop();
      }
      spinners[parseInt(monet_data['histo_number'])] = null ;
    })
    .fail(function(jqXHR){
      
      if ( jqXHR.responseJSON.number !== '-1' ) {
        var div_name = "#histo"+jqXHR.responseJSON.number;
        var output = "ERROR = " + jqXHR.responseJSON.error;
        $(div_name).html(output);

        spinners[parseInt(jqXHR.responseJSON.number)].stop();
        spinners[parseInt(jqXHR.responseJSON.number)] = null ;
      }
    })
    .always(function(monet_data){
    }) ;
  }
}

function load_dashboard(node_id, alarm_id, comparison_run, comparison_fill) {

  var is_page_documentation = window.location.href.indexOf("page_documentation") !== -1;

  if ( ! is_page_documentation ) {
    $(".spinner").remove();

    var _highlight = highlight_histo;

    if (spinner) spinner.stop();
    if (typeof node_id == "undefined" || is_folder_by_id(node_id)) return;

    var target = document.getElementById('maincontainer');
    if (spinner === null) { 
      spinner = new Spinner(small_spinner_opts).spin( target ) ;
    }; 
    spinner.spin( target );

    for (var i = 0 ; i < 30 ; i++ ) {
      if (spinners[i] != null ) spinners[i].stop();
      spinners[i] = null ;
    }
  
    var is_online = window.location.href.indexOf("online_dq") !== -1;
    var is_sim = window.location.href.indexOf("sim_dq") !== -1;
    var is_history = window.location.href.indexOf("history_dq") !== -1;
    var is_offlinedq = window.location.href.indexOf("offline_dq") !== -1;
    var is_trend = window.location.href.indexOf("trends") !== -1;

    if (alarm_id) data_source = "alarm";
    else if (is_online) data_source = "online";
    else if (is_sim) data_source = "sim_dq";
    else if (is_history) data_source = "history";
    else if (is_trend) data_source = "trends";
    else data_source = "offline";

    var compare_with_run = -1;
    if (comparison_run) compare_with_run = comparison_run;

    var compare_with_fill = -1;
    if (comparison_fill) compare_with_fill = comparison_fill;

    var procpass = null;
    var partition = null;
    var run_number = 0;
    var history_type = '';

    if ( is_history || is_offlinedq ) {
      run_number = $("#runNmbrTextfield").val();
      history_type = $("#source-type-field").val();
    } else if ( is_online ) {
      $.ajax({
        type: "GET",
        cache: false,
        async: false,
        url: "/online_runnumber?mode=online&partition="+$("#partition-field").val(),
        success: function(server_reply) { 
          run_number = server_reply.run_number ;
        }, 
        error: function(response) {
          run_number = 0 ;
        }
      });
    }

    if (is_sim) {
      run_number = $("#runNmbrTextfield").val();
      var event_type = $("#evtSelect").val();
      var sim_hist_file = $("#fileSelect").val();
    } else {
      var event_type = null;
      var sim_hist_file = null;
    }

    var ref_state = $("#changeReferenceMode").data("state");
    if ($("#proc-pass-field").length) {
      // check if processing pass field exists
      procpass = $("#proc-pass-field").val();
    }
    if ($("#partition-field").length) {
      // check if partition field exists
      partition = $("#partition-field").val();
    }

    let trend_duration = is_online ? $("#trend-duration-field").val() : "0";

    var req = {
      data_source: data_source,
      path: node_id,
      reference: ref_state,
      is_online: is_online,
      procpass: procpass,
      partition: partition,
      highlight_histo: _highlight,
      run_number: run_number,
      alarm_id: alarm_id,
      trend_duration: trend_duration,
      event_type: event_type,
      sim_hist_file: sim_hist_file,
      history_type: history_type,
      compare_with_run: compare_with_run,
      compare_with_fill: compare_with_fill
    };

    if (data_source == "history" && $("#source-type-field").val() == "Interval") {
      req.data_source = "history_interval";
      req.interval_begin = $("#interval-begin")
        .data("DateTimePicker")
        .date()
        .format(date_format);
      req.interval_size = $("#interval-size")
        .data("DateTimePicker")
        .date()
        .format("HH:mm");
    }

    if (data_source == "trends") {
      delete req['reference'];
      delete req['is_online'];
      delete req['procpass'];
      delete req['partition'];
      delete req['highlight_histo'];
      delete req['run_number'];
      delete req['alarm_id'];
      delete req['trend_duration'];
      delete req['event_type'];
      delete req['sim_hist_file'];
      if ($("#source-type-field").val() == "Runs") {
        req['run_number_min'] = $("#runNmbrTextfieldFrom").val() ;
        req['run_number_max'] = $("#runNmbrTextfieldTo").val() ;
      } else {
        req['fill_number_min'] = $("#runNmbrTextfieldFrom").val() ;
        req['fill_number_max'] = $("#runNmbrTextfieldTo").val() ;
      }
    }
  }

  const date = new Date().toLocaleDateString();
  if ( ! is_page_documentation ) {
    var output = mustache.render(page_template, {'path': node_id});
  } else {
    var output = mustache.render(page_template_for_doc, {'path': node_id});
  }

  $("#main").html(output);

  if ( ! is_page_documentation ) {
    $.ajax( {
      url: "histo_list",
      method: "GET",
      dataType: "json",
      data: { data_source: data_source,
              path: node_id },
    })
    .done(function( data ) {
      var histo_list = data.histo_list;
      var key_list = data.key_list;
      var hist_dict = {};
      var key_dict = {};
      var number_dict = {};
      var output_description = '';
      var output = '';
      output = mustache.render(pagedoc_template, {'pagedoc': data.pagedoc});
      $("#collapsed_page_info").html(output);
      output = '' ;
      for ( var i = 0; i < histo_list.length; i++ ){
        if (('motherh' in histo_list[i]) && ( (histo_list[i]['motherh'] !== null) && (histo_list[i]['motherh'] !== '') ) ) {
          continue;
        }
        hist_dict[ histo_list[i]["name"] ] = JSON.stringify( histo_list[i] ) ;
        key_dict[ histo_list[i]["name"] ] = JSON.stringify( key_list[i] ) ;
        number_dict[ histo_list[i]["name"] ] = i;
        output += "<div id=\"histo"+i.toString()+"\"></div>";
        output_description += "<div id=\"histo-description"+i.toString()+"\"></div>";
      }

      var task_names = [] ;
      for ( var i = 0; i < histo_list.length; i++ ){
        if (('motherh' in histo_list[i]) && ( (histo_list[i]['motherh'] !== null) && (histo_list[i]['motherh'] !== '') ) ) {
          hist_dict[ histo_list[i]["motherh"] ] = hist_dict[ histo_list[i]["motherh"] ] + "," + JSON.stringify( histo_list[i] ) ;
          key_dict[ histo_list[i]["motherh"] ] = key_dict[ histo_list[i]["motherh"] ] + "," + JSON.stringify( key_list[i] ) ;
        }
        var task_name = histo_list[i]["taskname"] ;
        if ( histo_list[i].hasOwnProperty("operation")) {
          for ( var j = 0; j < histo_list[i]["operation"]["inputs"].length; j++) {
            task_names.push( histo_list[i]["operation"]["inputs"][j]["taskname"] );
          }
        } else if ( ! task_name.startsWith("WinCC/") ) {
          task_names.push( task_name );
        } 
      }
      $("#svg-canvas").html(output);
      $("#description-list").html(output_description);
      delete req['path'];

      // in history or offline DQ modes check if histograms exist already
      if ( (data_source == "history") && (task_names.length != 0 )) {
        req['tasks'] = task_names;
        $.ajax({
          async: true,
          timeout: 10000,
          tryCount: 0,
          retryLimit: 0,  
          type: "POST",
          url: "prepare_files",
          data: req,
        })
        .done(function(monet_data){
          if ( monet_data.message != "all files are ready")
            alert(monet_data.message);
          load_histograms( hist_dict , req , key_dict , number_dict );
          if (spinner) {
            spinner.stop();
          }
        })
        .fail(function(jqXHR){
          spinner.stop();
          alert(jqXHR.responseJSON.error);
        });
      } else {
        load_histograms( hist_dict , req , key_dict , number_dict );
        spinner.stop();
      }
    })
    .fail(function( data ) {
      var output = mustache.render(error_template, data.responseJSON );
      $("#main").html(output);
      spinner.stop();
    })
    .always( function() {
      //spinner.stop();
    }) ;
  }
  else { 
    $.ajax( {
      url: "histo_list",
      method: "GET",
      dataType: "json",
      data: { data_source: "page_documentation",
              path: node_id },
    })
    .done(function( data ) {
      var output = '';
      output = mustache.render(pagedoc_template_for_doc, {'pagedoc': data.pagedoc});
      $("#svg-canvas").html(output);
    })
    .fail(function( data ) {
      var output = mustache.render(error_template, data.responseJSON );
      $("#main").html(output);
    })
    .always( function() {
    }) ;
  }

  window.last_dashboard_node_id = node_id;
}

function selectNode(e, data) {
  if (!is_folder_by_id(data.node.id))
    load_dashboard(data.node.id, undefined, undefined, undefined);
}

function openNode(e, data) {
  if (is_folder_by_id(data.node.id)) {
    var d = document.getElementById(data.node.id);

    var object = $(d)
      .children("a")
      .children("i");

    //Create ajax call to save tree state
    $.ajax({
      url: "menu_tree_open_or_close_folder",
      async: true,
      type: "GET",
      data: {
        id: data.node.id,
        action: "open"
      },
      contentType: "application/json; charset=utf-8",
      success: function(json) {
        localStorage.setItem("menutree_timestamp", json["menutree_timestamp"]);
        localStorage.setItem(
          "menutree_json",
          JSON.stringify(
            $("#menuTree")
              .jstree(true)
              .get_json("#", { flat: false })
          )
        );
      },
      error: function(xhr, ajaxOptions, thrownError) {
        alert("JSON Error:" + JSON.stringify(xhr) + ajaxOptions + thrownError);
      }
    });
  }
}

function closeNode(e, data) {
  if (is_folder_by_id(data.node.id)) {
    var d = document.getElementById(data.node.id);

    var object = $(d)
      .children("a")
      .children("i");

    //Create ajax call to save tree state
    $.ajax({
      url: "menu_tree_open_or_close_folder",
      async: true,
      type: "GET",
      data: {
        id: data.node.id,
        action: "close"
      },
      contentType: "application/json; charset=utf-8",
      success: function(json) {
        localStorage.setItem("menutree_timestamp", json["menutree_timestamp"]);
        localStorage.setItem(
          "menutree_json",
          JSON.stringify(
            $("#menuTree")
              .jstree(true)
              .get_json("#", { flat: false })
          )
        );
      },
      error: function(xhr, ajaxOptions, thrownError) {
        alert("JSON Error:" + JSON.stringify(xhr) + ajaxOptions + thrownError);
      }
    });
  }
}

export function reloadTree(event, data) {
  $("#menuTree").jstree("destroy");
  localStorage.removeItem("menutree_json");
  $("#loading").css("display", "block");
  treeAjaxCall(true, "closed", false, "");
}

function openAllTree() {
  $("#menuTree").jstree("destroy");
  $("#loading").css("display", "block");
  treeAjaxCall(true, "opened", false, "");
}

function closeAllTree() {
  $("#menuTree").jstree("destroy");
  $("#loading").css("display", "block");
  treeAjaxCall(true, "closed", false, "");
}

function addFilter() {
  var filter = $("#filterTextfield").val();
  $("#menuTree").jstree("destroy");
  $("#loading").css("display", "block");
  treeAjaxCall(true, "opened", true, filter);
}

function removeFilter() {
  $("#filterTextfield").val("");
  $("#menuTree").jstree("destroy");
  $("#loading").css("display", "block");
  treeAjaxCall(true, "closed", false, "");
}

function createJSTrees(jsonData) {
  $("#menuTree").jstree({
    core: {
      animation: 1,
      data: jsonData,
      dblclick_toggle: false
    }
  });

  $("#menuTree").off("open_node.jstree"); 
  $("#menuTree").off("close_node.jstree");
  $("#menuTree").off("select_node.jstree");
  $("#menuTree").off("ready.jstree");
  $("#menuTree").off("loaded.jstree");

  $("#menuTree").on("open_node.jstree", function(event, data) {
    openNode(event, data);
  });
  $("#menuTree").on("close_node.jstree", function(event, data) {
    closeNode(event, data);
  });
  $("#menuTree").on("activate_node.jstree", function(event, data) {
    $("#menuTree").jstree("toggle_node", data.node.id);
    selectNode(event, data);
  });


  $("#menuTree").bind("loaded.jstree", function(event, data) {
    // Patrick Robbe: already created in the dq.html file
    //$("#reloadTreeButton").click(function() {
    //  reloadTree();
    //});
    $("#openAllTreeButton").click(function() {
      openAllTree();
    });
    $("#closeAllTreeButton").click(function() {
      closeAllTree();
    });
  });
  $("#menuTree").bind("ready.jstree", function(e, data) {
    var node_to_select = unescape(getUrlParameter("selected_page")).replace(
      new RegExp("\\+", "g"),
      " "
    );
    if (node_to_select != "undefined") {
      window.last_dashboard_node_id = node_to_select;
      document.getElementById(node_to_select + "_anchor").click();
      // $(".jstree-container-ul").jstree(true).select_node(node_to_select);
    }
  });

  $("#loading").css("display", "none");
}

$(function() {
  treeAjaxCall(false, "closed", false, "");
});

export function showNextDashboard() {
  if (typeof window.last_dashboard_node_id == "undefined") return;
  var leaf = document.getElementById(window.last_dashboard_node_id);

  //deselect tree element (remove blue background)
  $("#menuTree").jstree("deselect_node", leaf);

  //step forward until you land on a leaf (not folder). Turn once at least.
  while (true) {
    if (leaf.nextSibling != null) leaf = leaf.nextSibling;
    //next(last) = first
    else leaf = leaf.parentNode.childNodes[0];

    if (!is_folder_by_id(leaf.id)) break;
  }

  //select the new tree element
  $("#menuTree").jstree("activate_node", leaf);
}

export function showPrevDashboard() {
  if (typeof window.last_dashboard_node_id == "undefined") return;

  var leaf = document.getElementById(window.last_dashboard_node_id);

  //deselect tree element (remove blue background)
  $("#menuTree").jstree("deselect_node", leaf);

  //step backward until you land on a leaf (not folder). Step at least once
  while (true) {
    if (leaf.previousSibling != null) leaf = leaf.previousSibling;
    //prev(first) = last
    else
      leaf = leaf.parentNode.childNodes[leaf.parentNode.childElementCount - 1];

    if (!is_folder_by_id(leaf.id)) break;
  }
  //select the new tree element
  $("#menuTree").jstree("activate_node", leaf);
}
