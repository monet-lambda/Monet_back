var objectToString=Object.prototype.toString;var isArray=Array.isArray||function isArrayPolyfill(object){return objectToString.call(object)==="[object Array]"};function isFunction(object){return typeof object==="function"}function typeStr(obj){return isArray(obj)?"array":typeof obj}function escapeRegExp(string){return string.replace(/[\-\[\]{}()*+?.,\\\^$|#\s]/g,"\\$&")}function hasProperty(obj,propName){return obj!=null&&typeof obj==="object"&&propName in obj}function primitiveHasOwnProperty(primitive,propName){return primitive!=null&&typeof primitive!=="object"&&primitive.hasOwnProperty&&primitive.hasOwnProperty(propName)}var regExpTest=RegExp.prototype.test;function testRegExp(re,string){return regExpTest.call(re,string)}var nonSpaceRe=/\S/;function isWhitespace(string){return!testRegExp(nonSpaceRe,string)}var entityMap={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;","/":"&#x2F;","`":"&#x60;","=":"&#x3D;"};function escapeHtml(string){return String(string).replace(/[&<>"'`=\/]/g,function fromEntityMap(s){return entityMap[s]})}var whiteRe=/\s*/;var spaceRe=/\s+/;var equalsRe=/\s*=/;var curlyRe=/\s*\}/;var tagRe=/#|\^|\/|>|\{|&|=|!/;function parseTemplate(template,tags){if(!template)return[];var lineHasNonSpace=false;var sections=[];var tokens=[];var spaces=[];var hasTag=false;var nonSpace=false;var indentation="";var tagIndex=0;function stripSpace(){if(hasTag&&!nonSpace){while(spaces.length)delete tokens[spaces.pop()]}else{spaces=[]}hasTag=false;nonSpace=false}var openingTagRe,closingTagRe,closingCurlyRe;function compileTags(tagsToCompile){if(typeof tagsToCompile==="string")tagsToCompile=tagsToCompile.split(spaceRe,2);if(!isArray(tagsToCompile)||tagsToCompile.length!==2)throw new Error("Invalid tags: "+tagsToCompile);openingTagRe=new RegExp(escapeRegExp(tagsToCompile[0])+"\\s*");closingTagRe=new RegExp("\\s*"+escapeRegExp(tagsToCompile[1]));closingCurlyRe=new RegExp("\\s*"+escapeRegExp("}"+tagsToCompile[1]))}compileTags(tags||mustache.tags);var scanner=new Scanner(template);var start,type,value,chr,token,openSection;while(!scanner.eos()){start=scanner.pos;value=scanner.scanUntil(openingTagRe);if(value){for(var i=0,valueLength=value.length;i<valueLength;++i){chr=value.charAt(i);if(isWhitespace(chr)){spaces.push(tokens.length);indentation+=chr}else{nonSpace=true;lineHasNonSpace=true;indentation+=" "}tokens.push(["text",chr,start,start+1]);start+=1;if(chr==="\n"){stripSpace();indentation="";tagIndex=0;lineHasNonSpace=false}}}if(!scanner.scan(openingTagRe))break;hasTag=true;type=scanner.scan(tagRe)||"name";scanner.scan(whiteRe);if(type==="="){value=scanner.scanUntil(equalsRe);scanner.scan(equalsRe);scanner.scanUntil(closingTagRe)}else if(type==="{"){value=scanner.scanUntil(closingCurlyRe);scanner.scan(curlyRe);scanner.scanUntil(closingTagRe);type="&"}else{value=scanner.scanUntil(closingTagRe)}if(!scanner.scan(closingTagRe))throw new Error("Unclosed tag at "+scanner.pos);if(type==">"){token=[type,value,start,scanner.pos,indentation,tagIndex,lineHasNonSpace]}else{token=[type,value,start,scanner.pos]}tagIndex++;tokens.push(token);if(type==="#"||type==="^"){sections.push(token)}else if(type==="/"){openSection=sections.pop();if(!openSection)throw new Error('Unopened section "'+value+'" at '+start);if(openSection[1]!==value)throw new Error('Unclosed section "'+openSection[1]+'" at '+start)}else if(type==="name"||type==="{"||type==="&"){nonSpace=true}else if(type==="="){compileTags(value)}}stripSpace();openSection=sections.pop();if(openSection)throw new Error('Unclosed section "'+openSection[1]+'" at '+scanner.pos);return nestTokens(squashTokens(tokens))}function squashTokens(tokens){var squashedTokens=[];var token,lastToken;for(var i=0,numTokens=tokens.length;i<numTokens;++i){token=tokens[i];if(token){if(token[0]==="text"&&lastToken&&lastToken[0]==="text"){lastToken[1]+=token[1];lastToken[3]=token[3]}else{squashedTokens.push(token);lastToken=token}}}return squashedTokens}function nestTokens(tokens){var nestedTokens=[];var collector=nestedTokens;var sections=[];var token,section;for(var i=0,numTokens=tokens.length;i<numTokens;++i){token=tokens[i];switch(token[0]){case"#":case"^":collector.push(token);sections.push(token);collector=token[4]=[];break;case"/":section=sections.pop();section[5]=token[2];collector=sections.length>0?sections[sections.length-1][4]:nestedTokens;break;default:collector.push(token)}}return nestedTokens}function Scanner(string){this.string=string;this.tail=string;this.pos=0}Scanner.prototype.eos=function eos(){return this.tail===""};Scanner.prototype.scan=function scan(re){var match=this.tail.match(re);if(!match||match.index!==0)return"";var string=match[0];this.tail=this.tail.substring(string.length);this.pos+=string.length;return string};Scanner.prototype.scanUntil=function scanUntil(re){var index=this.tail.search(re),match;switch(index){case-1:match=this.tail;this.tail="";break;case 0:match="";break;default:match=this.tail.substring(0,index);this.tail=this.tail.substring(index)}this.pos+=match.length;return match};function Context(view,parentContext){this.view=view;this.cache={".":this.view};this.parent=parentContext}Context.prototype.push=function push(view){return new Context(view,this)};Context.prototype.lookup=function lookup(name){var cache=this.cache;var value;if(cache.hasOwnProperty(name)){value=cache[name]}else{var context=this,intermediateValue,names,index,lookupHit=false;while(context){if(name.indexOf(".")>0){intermediateValue=context.view;names=name.split(".");index=0;while(intermediateValue!=null&&index<names.length){if(index===names.length-1)lookupHit=hasProperty(intermediateValue,names[index])||primitiveHasOwnProperty(intermediateValue,names[index]);intermediateValue=intermediateValue[names[index++]]}}else{intermediateValue=context.view[name];lookupHit=hasProperty(context.view,name)}if(lookupHit){value=intermediateValue;break}context=context.parent}cache[name]=value}if(isFunction(value))value=value.call(this.view);return value};function Writer(){this.templateCache={_cache:{},set:function set(key,value){this._cache[key]=value},get:function get(key){return this._cache[key]},clear:function clear(){this._cache={}}}}Writer.prototype.clearCache=function clearCache(){if(typeof this.templateCache!=="undefined"){this.templateCache.clear()}};Writer.prototype.parse=function parse(template,tags){var cache=this.templateCache;var cacheKey=template+":"+(tags||mustache.tags).join(":");var isCacheEnabled=typeof cache!=="undefined";var tokens=isCacheEnabled?cache.get(cacheKey):undefined;if(tokens==undefined){tokens=parseTemplate(template,tags);isCacheEnabled&&cache.set(cacheKey,tokens)}return tokens};Writer.prototype.render=function render(template,view,partials,config){var tags=this.getConfigTags(config);var tokens=this.parse(template,tags);var context=view instanceof Context?view:new Context(view,undefined);return this.renderTokens(tokens,context,partials,template,config)};Writer.prototype.renderTokens=function renderTokens(tokens,context,partials,originalTemplate,config){var buffer="";var token,symbol,value;for(var i=0,numTokens=tokens.length;i<numTokens;++i){value=undefined;token=tokens[i];symbol=token[0];if(symbol==="#")value=this.renderSection(token,context,partials,originalTemplate,config);else if(symbol==="^")value=this.renderInverted(token,context,partials,originalTemplate,config);else if(symbol===">")value=this.renderPartial(token,context,partials,config);else if(symbol==="&")value=this.unescapedValue(token,context);else if(symbol==="name")value=this.escapedValue(token,context,config);else if(symbol==="text")value=this.rawValue(token);if(value!==undefined)buffer+=value}return buffer};Writer.prototype.renderSection=function renderSection(token,context,partials,originalTemplate,config){var self=this;var buffer="";var value=context.lookup(token[1]);function subRender(template){return self.render(template,context,partials,config)}if(!value)return;if(isArray(value)){for(var j=0,valueLength=value.length;j<valueLength;++j){buffer+=this.renderTokens(token[4],context.push(value[j]),partials,originalTemplate,config)}}else if(typeof value==="object"||typeof value==="string"||typeof value==="number"){buffer+=this.renderTokens(token[4],context.push(value),partials,originalTemplate,config)}else if(isFunction(value)){if(typeof originalTemplate!=="string")throw new Error("Cannot use higher-order sections without the original template");value=value.call(context.view,originalTemplate.slice(token[3],token[5]),subRender);if(value!=null)buffer+=value}else{buffer+=this.renderTokens(token[4],context,partials,originalTemplate,config)}return buffer};Writer.prototype.renderInverted=function renderInverted(token,context,partials,originalTemplate,config){var value=context.lookup(token[1]);if(!value||isArray(value)&&value.length===0)return this.renderTokens(token[4],context,partials,originalTemplate,config)};Writer.prototype.indentPartial=function indentPartial(partial,indentation,lineHasNonSpace){var filteredIndentation=indentation.replace(/[^ \t]/g,"");var partialByNl=partial.split("\n");for(var i=0;i<partialByNl.length;i++){if(partialByNl[i].length&&(i>0||!lineHasNonSpace)){partialByNl[i]=filteredIndentation+partialByNl[i]}}return partialByNl.join("\n")};Writer.prototype.renderPartial=function renderPartial(token,context,partials,config){if(!partials)return;var tags=this.getConfigTags(config);var value=isFunction(partials)?partials(token[1]):partials[token[1]];if(value!=null){var lineHasNonSpace=token[6];var tagIndex=token[5];var indentation=token[4];var indentedValue=value;if(tagIndex==0&&indentation){indentedValue=this.indentPartial(value,indentation,lineHasNonSpace)}var tokens=this.parse(indentedValue,tags);return this.renderTokens(tokens,context,partials,indentedValue,config)}};Writer.prototype.unescapedValue=function unescapedValue(token,context){var value=context.lookup(token[1]);if(value!=null)return value};Writer.prototype.escapedValue=function escapedValue(token,context,config){var escape=this.getConfigEscape(config)||mustache.escape;var value=context.lookup(token[1]);if(value!=null)return typeof value==="number"&&escape===mustache.escape?String(value):escape(value)};Writer.prototype.rawValue=function rawValue(token){return token[1]};Writer.prototype.getConfigTags=function getConfigTags(config){if(isArray(config)){return config}else if(config&&typeof config==="object"){return config.tags}else{return undefined}};Writer.prototype.getConfigEscape=function getConfigEscape(config){if(config&&typeof config==="object"&&!isArray(config)){return config.escape}else{return undefined}};var mustache={name:"mustache.js",version:"4.2.0",tags:["{{","}}"],clearCache:undefined,escape:undefined,parse:undefined,render:undefined,Scanner:undefined,Context:undefined,Writer:undefined,set templateCache(cache){defaultWriter.templateCache=cache},get templateCache(){return defaultWriter.templateCache}};var defaultWriter=new Writer;mustache.clearCache=function clearCache(){return defaultWriter.clearCache()};mustache.parse=function parse(template,tags){return defaultWriter.parse(template,tags)};mustache.render=function render(template,view,partials,config){if(typeof template!=="string"){throw new TypeError('Invalid template! Template should be a "string" '+'but "'+typeStr(template)+'" was given as the first '+"argument for mustache#render(template, view, partials)")}return defaultWriter.render(template,view,partials,config)};mustache.escape=escapeHtml;mustache.Scanner=Scanner;mustache.Context=Context;mustache.Writer=Writer;export default mustache;export function getUrlParameter(sParam){var sPageURL=decodeURIComponent(window.location.search.substring(1)),sURLVariables=sPageURL.split("&"),sParameterName,i;for(i=0;i<sURLVariables.length;i++){sParameterName=sURLVariables[i].split("=");if(sParameterName[0]===sParam){return sParameterName[1]===undefined?true:sParameterName[1];}}};var readFromDB=false;var data_source="offline";var div_template=`<div style="position: absolute; left: {{cx}}px; top: {{cy}}px; width: {{sx}}px; height: {{sy}}px;">{{{div}}}</div>`;var page_template=`
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
</script>`;var page_template_for_doc=`
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
var pagedoc_template=`
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
var pagedoc_template_for_doc=`
<div class="panel-body">
            <p>
                {{{pagedoc}}}
            </p>
        </div>
`
var error_template=`
<div id="svg-canvas">
<h4>Error while loading page</h4>
    <pre>{{error}}</pre>
</div>
`;export function page_init(){setTimeout(function(){mustache.parse(div_template);mustache.parse(page_template);mustache.parse(error_template);mustache.parse(pagedoc_template);},0);}
function treeAjaxCall(enforceReadFromDBFlag,allNodesStandardState,filterFlag,filter){readFromDB=enforceReadFromDBFlag||window.pageNormallyReadFromDBFlag;var menutree_json=localStorage.getItem("menutree_json");if(menutree_json!="undefined"&&menutree_json){createJSTrees(JSON.parse(menutree_json));}
$.ajax({async:true,type:"GET",url:"menutree",dataType:"json",data:{loadFromDBFlag:readFromDB,allNodesStandardState:allNodesStandardState,filterFlag:filterFlag,filter:filter,menutree_timestamp:localStorage.getItem("menutree_timestamp")},success:function(json){if(!json["current_actual"]){createJSTrees(json["menutree_json"]);localStorage.setItem("menutree_json",JSON.stringify(json["menutree_json"]));localStorage.setItem("menutree_timestamp",json["menutree_timestamp"]);}},error:function(xhr,ajaxOptions,thrownError){alert("Tree menu loading error:"+thrownError);}});}
function is_folder_by_id(id){return String(id).indexOf("//F//")==0;}
var spinner=null;var spinners=new Array(30);var small_spinner_opts={lines:13,length:20,width:10,radius:10,corners:1,rotate:0,direction:1,color:"#000",speed:1,trail:60,shadow:false,hwaccel:false,className:"spinner",zIndex:2e9,top:"15%",left:"50%"};function load_histograms(hist_dict,req,key_dict,number_dict){for(const[key,value]of Object.entries(hist_dict)){req['histos_contained']="["+value+"]";req['key_list']="["+key_dict[key]+"]";req['histo_number']=number_dict[key];var target=document.getElementById("maincontainer");spinners[number_dict[key]]=new Spinner(small_spinner_opts).spin(target);$.ajax({async:true,timeout:150000,tryCount:0,retryLimit:0,type:"POST",url:"single_histo",data:req,}).done(function(monet_data){var h_cx=monet_data.divs[0].size[0];var h_cy=monet_data.divs[0].size[1];var h_sx=monet_data.divs[0].size[2];var h_sy=monet_data.divs[0].size[3];var canvas_height=0.85*$("#sidebar").height();var canvas_width=$(window).width()-$("#sidebar").width();var base_height=Math.max(canvas_height,300);var base_width=Math.max(canvas_width,800);var div_params={cx:Math.floor(base_width*h_cx),cy:Math.floor(base_height*(1.0-h_sy)+20),sx:Math.floor(0.95*base_width*(h_sx-h_cx)),sy:Math.floor(0.95*base_height*(h_sy-h_cy)),div:monet_data.divs[0].code,};var div_name="#histo"+monet_data['histo_number'];var output=mustache.render(div_template,div_params);$(div_name).html(output);var div_description_name="#histo-description"+monet_data['histo_number'];$(div_description_name).html(monet_data['pagedoc']);const fn=new Function(monet_data.script);fn();if(spinners[parseInt(monet_data['histo_number'])]){spinners[parseInt(monet_data['histo_number'])].stop();}
spinners[parseInt(monet_data['histo_number'])]=null;}).fail(function(jqXHR){if(jqXHR.responseJSON.number!=='-1'){var div_name="#histo"+jqXHR.responseJSON.number;var output="ERROR = "+jqXHR.responseJSON.error;$(div_name).html(output);spinners[parseInt(jqXHR.responseJSON.number)].stop();spinners[parseInt(jqXHR.responseJSON.number)]=null;}}).always(function(monet_data){});}}
function load_dashboard(node_id,alarm_id,comparison_run,comparison_fill){var is_page_documentation=window.location.href.indexOf("page_documentation")!==-1;if(!is_page_documentation){$(".spinner").remove();var _highlight=highlight_histo;if(spinner)spinner.stop();if(typeof node_id=="undefined"||is_folder_by_id(node_id))return;var target=document.getElementById('maincontainer');if(spinner===null){spinner=new Spinner(small_spinner_opts).spin(target);};spinner.spin(target);for(var i=0;i<30;i++){if(spinners[i]!=null)spinners[i].stop();spinners[i]=null;}
var is_online=window.location.href.indexOf("online_dq")!==-1;var is_sim=window.location.href.indexOf("sim_dq")!==-1;var is_history=window.location.href.indexOf("history_dq")!==-1;var is_offlinedq=window.location.href.indexOf("offline_dq")!==-1;var is_trend=window.location.href.indexOf("trends")!==-1;if(alarm_id)data_source="alarm";else if(is_online)data_source="online";else if(is_sim)data_source="sim_dq";else if(is_history)data_source="history";else if(is_trend)data_source="trends";else data_source="offline";var compare_with_run=-1;if(comparison_run)compare_with_run=comparison_run;var compare_with_fill=-1;if(comparison_fill)compare_with_fill=comparison_fill;var procpass=null;var partition=null;var run_number=0;var history_type='';if(is_history||is_offlinedq){run_number=$("#runNmbrTextfield").val();history_type=$("#source-type-field").val();}else if(is_online){$.ajax({type:"GET",cache:false,async:false,url:"/online_runnumber?mode=online&partition="+$("#partition-field").val(),success:function(server_reply){run_number=server_reply.run_number;},error:function(response){run_number=0;}});}
if(is_sim){run_number=$("#runNmbrTextfield").val();var event_type=$("#evtSelect").val();var sim_hist_file=$("#fileSelect").val();}else{var event_type=null;var sim_hist_file=null;}
var ref_state=$("#changeReferenceMode").data("state");if($("#proc-pass-field").length){procpass=$("#proc-pass-field").val();}
if($("#partition-field").length){partition=$("#partition-field").val();}
let trend_duration=is_online?$("#trend-duration-field").val():"0";var req={data_source:data_source,path:node_id,reference:ref_state,is_online:is_online,procpass:procpass,partition:partition,highlight_histo:_highlight,run_number:run_number,alarm_id:alarm_id,trend_duration:trend_duration,event_type:event_type,sim_hist_file:sim_hist_file,history_type:history_type,compare_with_run:compare_with_run,compare_with_fill:compare_with_fill};if(data_source=="history"&&$("#source-type-field").val()=="Interval"){req.data_source="history_interval";req.interval_begin=$("#interval-begin").data("DateTimePicker").date().format(date_format);req.interval_size=$("#interval-size").data("DateTimePicker").date().format("HH:mm");}
if(data_source=="trends"){delete req['reference'];delete req['is_online'];delete req['procpass'];delete req['partition'];delete req['highlight_histo'];delete req['run_number'];delete req['alarm_id'];delete req['trend_duration'];delete req['event_type'];delete req['sim_hist_file'];if($("#source-type-field").val()=="Runs"){req['run_number_min']=$("#runNmbrTextfieldFrom").val();req['run_number_max']=$("#runNmbrTextfieldTo").val();}else{req['fill_number_min']=$("#runNmbrTextfieldFrom").val();req['fill_number_max']=$("#runNmbrTextfieldTo").val();}}}
const date=new Date().toLocaleDateString();if(!is_page_documentation){var output=mustache.render(page_template,{'path':node_id});}else{var output=mustache.render(page_template_for_doc,{'path':node_id});}
$("#main").html(output);if(!is_page_documentation){$.ajax({url:"histo_list",method:"GET",dataType:"json",data:{data_source:data_source,path:node_id},}).done(function(data){var histo_list=data.histo_list;var key_list=data.key_list;var hist_dict={};var key_dict={};var number_dict={};var output_description='';var output='';output=mustache.render(pagedoc_template,{'pagedoc':data.pagedoc});$("#collapsed_page_info").html(output);output='';for(var i=0;i<histo_list.length;i++){if(('motherh'in histo_list[i])&&((histo_list[i]['motherh']!==null)&&(histo_list[i]['motherh']!==''))){continue;}
hist_dict[histo_list[i]["name"]]=JSON.stringify(histo_list[i]);key_dict[histo_list[i]["name"]]=JSON.stringify(key_list[i]);number_dict[histo_list[i]["name"]]=i;output+="<div id=\"histo"+i.toString()+"\"></div>";output_description+="<div id=\"histo-description"+i.toString()+"\"></div>";}
var task_names=[];for(var i=0;i<histo_list.length;i++){if(('motherh'in histo_list[i])&&((histo_list[i]['motherh']!==null)&&(histo_list[i]['motherh']!==''))){hist_dict[histo_list[i]["motherh"]]=hist_dict[histo_list[i]["motherh"]]+","+JSON.stringify(histo_list[i]);key_dict[histo_list[i]["motherh"]]=key_dict[histo_list[i]["motherh"]]+","+JSON.stringify(key_list[i]);}
var task_name=histo_list[i]["taskname"];if(histo_list[i].hasOwnProperty("operation")){for(var j=0;j<histo_list[i]["operation"]["inputs"].length;j++){task_names.push(histo_list[i]["operation"]["inputs"][j]["taskname"]);}}else if(!task_name.startsWith("WinCC/")){task_names.push(task_name);}}
$("#svg-canvas").html(output);$("#description-list").html(output_description);delete req['path'];if((data_source=="history")&&(task_names.length!=0)){req['tasks']=task_names;$.ajax({async:true,timeout:10000,tryCount:0,retryLimit:0,type:"POST",url:"prepare_files",data:req,}).done(function(monet_data){if(monet_data.message!="all files are ready")
alert(monet_data.message);load_histograms(hist_dict,req,key_dict,number_dict);if(spinner){spinner.stop();}}).fail(function(jqXHR){spinner.stop();alert(jqXHR.responseJSON.error);});}else{load_histograms(hist_dict,req,key_dict,number_dict);spinner.stop();}}).fail(function(data){var output=mustache.render(error_template,data.responseJSON);$("#main").html(output);spinner.stop();}).always(function(){});}
else{$.ajax({url:"histo_list",method:"GET",dataType:"json",data:{data_source:"page_documentation",path:node_id},}).done(function(data){var output='';output=mustache.render(pagedoc_template_for_doc,{'pagedoc':data.pagedoc});$("#svg-canvas").html(output);}).fail(function(data){var output=mustache.render(error_template,data.responseJSON);$("#main").html(output);}).always(function(){});}
window.last_dashboard_node_id=node_id;}
function selectNode(e,data){if(!is_folder_by_id(data.node.id))
load_dashboard(data.node.id,undefined,undefined,undefined);}
function openNode(e,data){if(is_folder_by_id(data.node.id)){var d=document.getElementById(data.node.id);var object=$(d).children("a").children("i");$.ajax({url:"menu_tree_open_or_close_folder",async:true,type:"GET",data:{id:data.node.id,action:"open"},contentType:"application/json; charset=utf-8",success:function(json){localStorage.setItem("menutree_timestamp",json["menutree_timestamp"]);localStorage.setItem("menutree_json",JSON.stringify($("#menuTree").jstree(true).get_json("#",{flat:false})));},error:function(xhr,ajaxOptions,thrownError){alert("JSON Error:"+JSON.stringify(xhr)+ajaxOptions+thrownError);}});}}
function closeNode(e,data){if(is_folder_by_id(data.node.id)){var d=document.getElementById(data.node.id);var object=$(d).children("a").children("i");$.ajax({url:"menu_tree_open_or_close_folder",async:true,type:"GET",data:{id:data.node.id,action:"close"},contentType:"application/json; charset=utf-8",success:function(json){localStorage.setItem("menutree_timestamp",json["menutree_timestamp"]);localStorage.setItem("menutree_json",JSON.stringify($("#menuTree").jstree(true).get_json("#",{flat:false})));},error:function(xhr,ajaxOptions,thrownError){alert("JSON Error:"+JSON.stringify(xhr)+ajaxOptions+thrownError);}});}}
export function reloadTree(event,data){$("#menuTree").jstree("destroy");localStorage.removeItem("menutree_json");$("#loading").css("display","block");treeAjaxCall(true,"closed",false,"");}
function openAllTree(){$("#menuTree").jstree("destroy");$("#loading").css("display","block");treeAjaxCall(true,"opened",false,"");}
function closeAllTree(){$("#menuTree").jstree("destroy");$("#loading").css("display","block");treeAjaxCall(true,"closed",false,"");}
function addFilter(){var filter=$("#filterTextfield").val();$("#menuTree").jstree("destroy");$("#loading").css("display","block");treeAjaxCall(true,"opened",true,filter);}
function removeFilter(){$("#filterTextfield").val("");$("#menuTree").jstree("destroy");$("#loading").css("display","block");treeAjaxCall(true,"closed",false,"");}
function createJSTrees(jsonData){$("#menuTree").jstree({core:{animation:1,data:jsonData,dblclick_toggle:false}});$("#menuTree").off("open_node.jstree");$("#menuTree").off("close_node.jstree");$("#menuTree").off("select_node.jstree");$("#menuTree").off("ready.jstree");$("#menuTree").off("loaded.jstree");$("#menuTree").on("open_node.jstree",function(event,data){openNode(event,data);});$("#menuTree").on("close_node.jstree",function(event,data){closeNode(event,data);});$("#menuTree").on("activate_node.jstree",function(event,data){$("#menuTree").jstree("toggle_node",data.node.id);selectNode(event,data);});$("#menuTree").bind("loaded.jstree",function(event,data){$("#openAllTreeButton").click(function(){openAllTree();});$("#closeAllTreeButton").click(function(){closeAllTree();});});$("#menuTree").bind("ready.jstree",function(e,data){var node_to_select=unescape(getUrlParameter("selected_page")).replace(new RegExp("\\+","g")," ");if(node_to_select!="undefined"){window.last_dashboard_node_id=node_to_select;document.getElementById(node_to_select+"_anchor").click();}});$("#loading").css("display","none");}
$(function(){treeAjaxCall(false,"closed",false,"");});export function showNextDashboard(){if(typeof window.last_dashboard_node_id=="undefined")return;var leaf=document.getElementById(window.last_dashboard_node_id);$("#menuTree").jstree("deselect_node",leaf);while(true){if(leaf.nextSibling!=null)leaf=leaf.nextSibling;else leaf=leaf.parentNode.childNodes[0];if(!is_folder_by_id(leaf.id))break;}
$("#menuTree").jstree("activate_node",leaf);}
export function showPrevDashboard(){if(typeof window.last_dashboard_node_id=="undefined")return;var leaf=document.getElementById(window.last_dashboard_node_id);$("#menuTree").jstree("deselect_node",leaf);while(true){if(leaf.previousSibling!=null)leaf=leaf.previousSibling;else
leaf=leaf.parentNode.childNodes[leaf.parentNode.childElementCount-1];if(!is_folder_by_id(leaf.id))break;}
$("#menuTree").jstree("activate_node",leaf);}
window.last_dashboard_node_id=undefined;function disable_nav_bar(disabled){var buttons=$(".btn-default").each(function(){if(disabled){$(this).addClass("disabled");}else{$(this).removeClass("disabled");}});}
function update_reference_glyph(state){var glyphs={activated:'glyphicon-ok',deactivated:'glyphicon-remove'}
var icon=$('#changeReferenceModeIcon')
icon.attr('class','glyphicon '+glyphs[state])}
function init_reference_state_button(){var button=$('#changeReferenceMode')
var state=button.data('state')
update_reference_glyph(state)}
function change_reference_mode(){var button=$('#changeReferenceMode')
var current_state=button.data('state')
var new_state={deactivated:'activated',activated:'deactivated'}[current_state]
$.ajax({async:true,type:'GET',url:'change_reference_state',data:{state:new_state},success:function(json){update_reference_glyph(new_state)
button.data('state',new_state)
if(window.last_dashboard_node_id)
document.getElementById(window.last_dashboard_node_id+'_anchor').click()},error:function(xhr,ajaxOptions,thrownError){alert('/change_reference_state error:'+thrownError)
set_status_field('','danger')}})}
function set_status_field(message,status){$('#statusForm').show()
$('#statusIndicatorContainer').removeClass('btn-success')
$('#statusIndicatorContainer').removeClass('btn-danger')
$('#statusIndicatorContainer').removeClass('btn-info')
$('#statusIndicatorContainer').removeClass('btn-warning')
$('#statusIndicatorIcon').removeClass('glyphicon-ok')
$('#statusIndicatorIcon').removeClass('glyphicon-exclamation-sign')
$('#statusIndicatorIcon').removeClass('glyphicon-question-sign')
if(status=='warning'){$('#statusIndicatorContainer').addClass('btn-warning')
$('#statusIndicatorIcon').addClass('glyphicon-exclamation-sign')}else if(status=='danger'){$('#statusIndicatorContainer').addClass('btn-danger')
$('#statusIndicatorIcon').addClass('glyphicon-exclamation-sign')}else if(status=='info'){$('#statusIndicatorContainer').addClass('btn-info')
$('#statusIndicatorIcon').addClass('glyphicon-exclamation-sign')}else if(status=='success'){$('#statusIndicatorContainer').addClass('btn-success')
$('#statusIndicatorIcon').addClass('glyphicon-ok')}else{alert('Unrecognised Status for status field!')}
$('#statusIndicatorText').text(message)}
export function compare_with_run(){let compare_run=prompt("Enter run number")
if(compare_run==null)return
if(window.last_dashboard_node_id){load_dashboard(window.last_dashboard_node_id,undefined,compare_run,undefined);}}
export function compare_with_fill(){let compare_fill=prompt("Enter fill number")
if(compare_fill==null)return
if(window.last_dashboard_node_id){load_dashboard(window.last_dashboard_node_id,undefined,undefined,compare_fill);}}
export function save_as_pdf(){html2canvas(document.getElementById("svg-canvas"),{height:document.getElementById("svg-canvas").scrollHeight+document.getElementById("pageheader").scrollHeight+60,windowHeight:document.getElementById("svg-canvas").scrollHeight+document.getElementById("pageheader").scrollHeight+60,scrollY:-window.scrollY}).then((canvas)=>{var file_name="documentation.png";var data_url=canvas.toDataURL("image/png");var evt_obj;var anchor=document.createElement("a");anchor.setAttribute("href",data_url);anchor.setAttribute("target","_blank");anchor.setAttribute("download",file_name);if(document.createEvent){evt_obj=document.createEvent("MouseEvents");evt_obj.initEvent("click",true,true);anchor.dispatchEvent(evt_obj);}else if(anchor.click){anchor.click();}});}