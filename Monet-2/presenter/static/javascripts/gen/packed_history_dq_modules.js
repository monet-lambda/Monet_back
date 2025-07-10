var __assign=this&&this.__assign||function(){__assign=Object.assign||function(t){for(var s,i=1,n=arguments.length;i<n;i++){s=arguments[i];for(var p in s)if(Object.prototype.hasOwnProperty.call(s,p))t[p]=s[p]}return t};return __assign.apply(this,arguments)};var defaults={lines:12,length:7,width:5,radius:10,scale:1,corners:1,color:"#000",fadeColor:"transparent",animation:"spinner-line-fade-default",rotate:0,direction:1,speed:1,zIndex:2e9,className:"spinner",top:"50%",left:"50%",shadow:"0 0 1px transparent",position:"absolute"};var Spinner=function(){function Spinner(opts){if(opts===void 0){opts={}}this.opts=__assign(__assign({},defaults),opts)}Spinner.prototype.spin=function(target){this.stop();this.el=document.createElement("div");this.el.className=this.opts.className;this.el.setAttribute("role","progressbar");this.el.style.position=this.opts.position;this.el.style.width="0";this.el.style.zIndex=this.opts.zIndex.toString();this.el.style.left=this.opts.left;this.el.style.top=this.opts.top;this.el.style.transform="scale(".concat(this.opts.scale,")");if(target){target.insertBefore(this.el,target.firstChild||null)}drawLines(this.el,this.opts);return this};Spinner.prototype.stop=function(){if(this.el){if(this.el.parentNode){this.el.parentNode.removeChild(this.el)}this.el=undefined}return this};return Spinner}();export{Spinner};function getColor(color,idx){return typeof color=="string"?color:color[idx%color.length]}function drawLines(el,opts){var borderRadius=Math.round(opts.corners*opts.width*500)/1e3+"px";var shadow="none";if(opts.shadow===true){shadow="0 2px 4px #000"}else if(typeof opts.shadow==="string"){shadow=opts.shadow}var shadows=parseBoxShadow(shadow);for(var i=0;i<opts.lines;i++){var degrees=~~(360/opts.lines*i+opts.rotate);var backgroundLine=document.createElement("div");backgroundLine.style.position="absolute";backgroundLine.style.top="".concat(-opts.width/2,"px");backgroundLine.style.width=opts.length+opts.width+"px";backgroundLine.style.height=opts.width+"px";backgroundLine.style.background=getColor(opts.fadeColor,i);backgroundLine.style.borderRadius=borderRadius;backgroundLine.style.transformOrigin="left";backgroundLine.style.transform="rotate(".concat(degrees,"deg) translateX(").concat(opts.radius,"px)");var delay=i*opts.direction/opts.lines/opts.speed;delay-=1/opts.speed;var line=document.createElement("div");line.style.width="100%";line.style.height="100%";line.style.background=getColor(opts.color,i);line.style.borderRadius=borderRadius;line.style.boxShadow=normalizeShadow(shadows,degrees);line.style.animation="".concat(1/opts.speed,"s linear ").concat(delay,"s infinite ").concat(opts.animation);backgroundLine.appendChild(line);el.appendChild(backgroundLine)}}function parseBoxShadow(boxShadow){var regex=/^\s*([a-zA-Z]+\s+)?(-?\d+(\.\d+)?)([a-zA-Z]*)\s+(-?\d+(\.\d+)?)([a-zA-Z]*)(.*)$/;var shadows=[];for(var _i=0,_a=boxShadow.split(",");_i<_a.length;_i++){var shadow=_a[_i];var matches=shadow.match(regex);if(matches===null){continue}var x=+matches[2];var y=+matches[5];var xUnits=matches[4];var yUnits=matches[7];if(x===0&&!xUnits){xUnits=yUnits}if(y===0&&!yUnits){yUnits=xUnits}if(xUnits!==yUnits){continue}shadows.push({prefix:matches[1]||"",x:x,y:y,xUnits:xUnits,yUnits:yUnits,end:matches[8]})}return shadows}function normalizeShadow(shadows,degrees){var normalized=[];for(var _i=0,shadows_1=shadows;_i<shadows_1.length;_i++){var shadow=shadows_1[_i];var xy=convertOffset(shadow.x,shadow.y,degrees);normalized.push(shadow.prefix+xy[0]+shadow.xUnits+" "+xy[1]+shadow.yUnits+shadow.end)}return normalized.join(", ")}function convertOffset(x,y,degrees){var radians=degrees*Math.PI/180;var sin=Math.sin(radians);var cos=Math.cos(radians);return[Math.round((x*cos+y*sin)*1e3)/1e3,Math.round((-x*sin+y*cos)*1e3)/1e3]}
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
var logbook_data={VELO:{MOptions:null,Options:"VELO",Level:null},MUON:{MOptions:null,Options:"MUON",Level:"Info, Warning, Severe",},"TestLogbook":{MOptions:"Test",Options:null,Level:null},"HLT":{MOptions:"HLT",Options:null,Level:null},Shift:{MOptions:null,Options:"LHCb, Velo, RICH1, UT, RICH2, RICH, SCIFI, CALO, ECAL, HCAL, MUON, PLUME, HLT1, HLT2, TFC, Magnet, LHC, DSS, Monitoring, Access, ONLINE, ALIGNMENT, CALIBRATION",Level:null},Online:{MOptions:null,Options:"DAQ",Level:null},"Data Quality":{MOptions:"Velo, PLUME, UT, RICH, CALO, MUON, HLT",Options:null,Level:null},RICH:{MOptions:"RICH, RICH1, RICH2",Options:null,Level:null},CALO:{MOptions:null,Options:"Calo, ECAL, HCAL",Level:null},"Alignment and calibration":{MOptions:null,Options:"RTA, Alignment, Calibration",Level:null},UT:{MOptions:null,Options:"UT",Level:null},SciFi:{MOptions:null,Options:"SciFi",Level:null},PLUME:{MOptions:null,Options:"PLUME",Level:null},BCM:{MOptions:null,Options:"Flux Report, Piquet Report, BCM, Dump Report, SBCM Development",Level:null}};var problemdb_subsystems=["VELO","UT","RICH1","SCIFI","ECAL","HCAL","MUON","ONLINE","RTA-HLT1","RTA-HTL2","RTA-AC","PLUME","SMOG","LUMI","BEAM"];var subsys_template=`
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
`;var level_template=`
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
`;function unique(arr){var u={},a=[];for(var i=0,l=arr.length;i<l;++i){if(!u.hasOwnProperty(arr[i])){a.push(arr[i]);u[arr[i]]=1;}}
return a;}
var save_refresh=true;export function show_elog_modal(){var is_online=window.location.href.indexOf("online_dq")!==-1;if(is_online){save_refresh=window._refresh_enabled;window._refresh_enabled=false;}
$("#elog-modal").modal({backdrop:"static",keyboard:false});$("#elog-modal").draggable({handle:".modal-header"});try{var run_number=$("#runNmbrTextfield").val();if(run_number==undefined){run_number='unknown';$.ajax({type:"GET",cache:false,async:false,url:"/online_runnumber?mode=online&partition="+$("#partition-field").val(),success:function(server_reply){run_number=server_reply.run_number;online_run_number=run_number;},error:function(response){run_number='unknown';}});}
$("#elog-text").val("\n\n---------\nRun #"+run_number);}catch(err){console.log(err);}
$("#elog-modal").modal("show");}
export function hide_elog_modal(){var current_logbook=$("#elog-logbook").val();$("#elog-text").val("");$("#elog-modal").modal("toggle");var is_online=window.location.href.indexOf("online_dq")!==-1;if(is_online){window._refresh_enabled=save_refresh;}}
var elog_spinner;function add_elog_spinner(){var opts={lines:13,length:10,width:5,radius:5,corners:1,rotate:0,direction:1,color:"#000",speed:1,trail:60,shadow:false,hwaccel:false,className:"spinner",zIndex:2e9,top:"200px",left:"auto"};var target=document.getElementById("maincontainer");elog_spinner=new Spinner(opts).spin(target);}
export function submit_to_elog(){if(elog_spinner)elog_spinner.stop();add_elog_spinner();var current_logbook=$("#elog-logbook").val();var checked_subsystems=get_selected_subsystems();var checked_level=get_selected_level();if(checked_level.length>0){checked_level=checked_level[0];}else{checked_level='';}
var problemdb_box=document.getElementById("problemdb-submit");var submit_to_problemdb="no";if(problemdb_box){submit_to_problemdb=problemdb_box.checked?"yes":"no";}
var run_number=$("#runNmbrTextfield").val();if(run_number==undefined&&typeof online_run_number!=="undefined"){run_number=online_run_number;}
var payload={logbook:$("#elog-logbook").val(),author:$("#elog-fullname").val(),subsystem:checked_subsystems.join(" | "),subject:$("#elog-subject").val(),run_number:run_number,level:checked_level,text:$("#elog-text").val(),images:[],submit_to_problemdb:submit_to_problemdb};if(!payload["subject"]){alert("Subject is mandatory");elog_spinner.stop();}else{html2canvas(document.getElementById("main"),{width:Math.max(document.getElementById("svg-canvas").scrollWidth,document.getElementById("pageheader").scrollWidth),height:document.getElementById("svg-canvas").scrollHeight+document.getElementById("pageheader").scrollHeight+60+document.getElementById("information-panel").offsetHeight,windowWidth:Math.max(document.getElementById("svg-canvas").scrollWidth+document.getElementById("pageheader").scrollWidth),windowHeight:document.getElementById("svg-canvas").scrollHeight+document.getElementById("pageheader").scrollHeight+60+document.getElementById("information-panel").offsetHeight,scrollX:-window.scrollX,scrollY:-window.scrollY}).then((canvas)=>{payload["images"].push(canvas.toDataURL("image/png"));$.ajax({type:"POST",url:"elog_submit",data:JSON.stringify(payload),contentType:"application/json; charset=utf-8",dataType:"json",success:function(data,statusText,jqXHR){if(data.ok==true){alert("Successfuly submitted!");elog_spinner.stop();hide_elog_modal();}else{alert("Error while submitting: `"+
data.message+"`. Ping us on lhcb-monet@cern.ch");elog_spinner.stop();}
elog_spinner.stop();},failure:function(jqXHR,textStatus,errorThrown){alert("Problem sending to ELOG");elog_spinner.stop();}});});}}
function get_logbook(){if(!$("#elog-logbook").length)return"";return $("#elog-logbook").val();}
function get_default_logbook(){var is_online=window.location.href.indexOf("online_dq")!==-1;var is_history=window.location.href.indexOf("history_dq")!==-1;if(is_online||is_history){return"Shift";}else{return"Data Quality";}}
function elog_init(){if(get_logbook()=="")return;var select_field_html="";var default_logbook=get_default_logbook();for(var logbook in logbook_data){if(!logbook_data.hasOwnProperty(logbook))continue;if(logbook!=default_logbook)
select_field_html+="<option>"+logbook+"</option>";else
select_field_html+='<option selected="selected">'+logbook+"</option>";}
$("#elog-logbook").html(select_field_html);logbook_show_subsys();var select=document.getElementById("elog-logbook");select.addEventListener("change",function(){logbook_show_subsys();});}
function get_selected_subsystems(){var boxes=document.getElementsByName("subsystem");var ret=[];for(var box of boxes){if(box.checked){ret.push(box.value);}}
return ret;}
function get_selected_level(){var boxes=document.getElementsByName("level");var ret=[];for(var box of boxes){if(box.checked){ret.push(box.value);}}
return ret;}
function logbook_show_subsys(){var current_logbook=$("#elog-logbook").val();var subsys_html='<label for="elog-system">Subsystem</label><br/>';var multiple=true;var subsystems=logbook_data[current_logbook].MOptions;var has_levels=true;var list_levels=logbook_data[current_logbook].Level;if(subsystems==null){multiple=false;subsystems=logbook_data[current_logbook].Options;}
if(list_levels==null){has_levels=false;}else{list_levels=list_levels.split(",").map(function(s){return s.trim();});}
if(subsystems==null){alert("Error loading subsystems!");return;}
subsystems=subsystems.split(",").map(function(s){return s.trim();});var left_part=[];var right_part=[];var is_notchecked_left_part=[];var is_notchecked_right_part=[];var is_checked_left_part=[];var is_checked_right_part=[];if(subsystems.length>1){var half_length=Math.ceil(subsystems.length/2);var left_part=subsystems.splice(0,half_length);var right_part=subsystems;}else{left_part=subsystems;}
left_part.forEach(function(item,index,array){is_notchecked_left_part.push({'text':item,'checked':''});is_checked_left_part.push({'text':item,'checked':''});});right_part.forEach(function(item,index,array){is_notchecked_right_part.push({'text':item,'checked':''});is_checked_right_part.push({'text':item,'checked':''});});if(subsystems.length>0){is_checked_left_part[0]={'text':is_checked_left_part[0]['text'],'checked':'checked'};}
var output=mustache.render(subsys_template,{subsystems_a:multiple?is_notchecked_left_part:is_checked_left_part,subsystems_b:multiple?is_notchecked_right_part:is_checked_right_part,selection_type:multiple?"checkbox":"radio"});$("#subsys-checkboxes").html(output);var select=document.getElementById("subsys-checkboxes");select.addEventListener("change",function(){verify_subsystem_choice_is_compatible_with_problemdb();});var level_vector=[];if(has_levels){list_levels.forEach(function(item,index,array){level_vector.push({'text':item,'checked':''});});if(list_levels.length>0){level_vector[0]={'text':level_vector[0]['text'],'checked':'checked'};}}
var output2=mustache.render(level_template,{title:has_levels?true:false,levels:level_vector,selection_type:"radio"});$("#level-checkboxes").html(output2);}
function verify_subsystem_choice_is_compatible_with_problemdb(){var box=document.getElementById("problemdb-submit");if(!box){return;}
let checked_subsystems=get_selected_subsystems();var all_good=checked_subsystems.length!=0;for(var ix in checked_subsystems){let subsystem=checked_subsystems[ix].trim();if(problemdb_subsystems.indexOf(subsystem)==-1){all_good=false;break;}}
$("#problemdb-submit").prop("disabled",!all_good);if(!all_good){$("#problemdb-submit").prop("checked",false);}}
$(function(){setTimeout(function(){mustache.parse(subsys_template);},0);elog_init();});window.last_dashboard_node_id=undefined;function disable_nav_bar(disabled){var buttons=$(".btn-default").each(function(){if(disabled){$(this).addClass("disabled");}else{$(this).removeClass("disabled");}});}
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
var date_format='MM/DD/YYYY HH:mm'
function decrease_run_number(){if($('#runNmbrTextfield').val()=='')return
if($('#source-type-field').val()=='Interval'){$('#interval-begin').data('DateTimePicker').date(get_diff_date(false))
set_new_run_number(parseInt($('#runNmbrTextfield').val()))
return}
var runnumber=parseInt($('#runNmbrTextfield').val())
$.ajax({async:true,type:'GET',url:'get_previous_runnumber?runnumber='+runnumber,success:function(json){if(!json.success){alert(json.data.message)
return}
set_new_run_number(json['data']['runnumber'])},error:function(xhr,ajaxOptions,thrownError){alert('Run switch error:'+thrownError)
set_status_field('JSON Error:'+thrownError,'danger')},complete:function(){disable_nav_bar(false)}})}
function increase_run_number(latest){var url=''
if(latest){url='get_latest_runnumber'}else{var runnumber=parseInt($('#runNmbrTextfield').val())
url='get_next_runnumber?runnumber='+runnumber
if($('#runNmbrTextfield').val()=='')return}
if($('#source-type-field').val()=='Interval'){if(latest){$('#interval-begin').data('DateTimePicker').maxDate(false)
$('#interval-begin').data('DateTimePicker').date(moment())
$('#interval-begin').data('DateTimePicker').date(get_diff_date(false))}else{$('#interval-begin').data('DateTimePicker').date(get_diff_date(true))}
set_new_run_number(0)
return}
$.ajax({async:true,type:'GET',url:url,success:function(json){if(!json.success){alert(json.data.message)
return}
set_new_run_number(json['data']['runnumber'])},error:function(xhr,ajaxOptions,thrownError){alert('Run switch error:'+thrownError)
set_status_field('JSON Error:'+thrownError,'danger')},complete:function(){disable_nav_bar(false)}})}
function get_diff_date(add){begin_date=$('#interval-begin').data('DateTimePicker').date()
diff_hours=$('#interval-size').data('DateTimePicker').date().hours()
diff_minutes=$('#interval-size').data('DateTimePicker').date().minutes()
if(add){return begin_date.add(diff_hours,'hours').add(diff_minutes,'minutes')}else{return begin_date.subtract(diff_hours,'hours').subtract(diff_minutes,'minutes')}}
function set_new_run_number(run_number){var url='browse_run?'
url+='run_number='+run_number
url+='&reference_state='+$('#changeReferenceMode').data('state')
url+='&selected_page='+$('.jstree-container-ul').jstree('get_selected')[0]
url+='&partition='+$('#partition-field').val()
if($('#source-type-field').val()=='Interval'){url+='&interval_begin='+
$('#interval-begin').data('DateTimePicker').date().format(date_format)
url+='&interval_size='+
$('#interval-size').data('DateTimePicker').date().format('HH:mm')
url+='&data_source='+'history_interval'}
window.location.href=url}
function set_run_to_ui_value(){set_new_run_number($('#runNmbrTextfield').val())}
$(function(){init_reference_state_button()
$('#changeReferenceMode').click(function(){change_reference_mode()})
var select=document.getElementById('partition-field')
select.addEventListener('change',function(){set_run_to_ui_value()})
$('#setRunNmbrButton').click(function(){set_run_to_ui_value()})
$('#runNmbrTextfield').keypress(function(e){if(e.keyCode==13){set_run_to_ui_value()}})
$('#decreaseRunNmbrButton').click(function(){decrease_run_number()})
$('#increaseRunNmbrButton').click(function(){increase_run_number(false)})
$('#increaseUncheckedRunNmbrButton').click(function(){increase_run_number(true)})})
function set_rundb_info(){var run_number=$('#runNmbrTextfield').val()
var fill_number=-1
if($('#source-type-field').val()=='Fill'){fill_number=run_number
run_number=-1}
$.ajax({async:true,type:'GET',url:'/rundb',data:{run:run_number,fill:fill_number},success:function(server_reply){if(!server_reply.success)return
var popover=$('#runInfo').data('bs.popover')
popover.options.html=true
popover.options.sanitize=false
popover.options.content=server_reply.rundb_info
var popover_is_visible=$('#runInfo').data('bs.popover').tip().hasClass('in')
if(popover_is_visible){$('#runInfo').popover('show')}}})}
$(document).ready(function(){var begin_date
var interval_size
if($('#interval-begin').val()){begin_date=moment($('#interval-begin').val(),date_format)}else{begin_date=moment().subtract(30,'minutes')}
if($('#interval-size').val()&&$('#interval-size').val()!='None'){interval_size=$('#interval-size').val()}else{interval_size='00:30'}
$('#interval-begin').datetimepicker({maxDate:moment(),format:'Fro\\m '+date_format,sideBySide:true,useStrict:true,date:begin_date})
$('#interval-size').datetimepicker({format:'for H:mm',date:moment(interval_size,'HH:mm')})
if($('#source-type-field').val()=='Interval'){$('#partition-field').show()}else{$('#partition-field').hide()}
$('#source-type-field').change(function(){Cookies.set('source-type-field',$(this).val(),{sameSite:'Lax'})
if($(this).val()=='Interval'){$('.history_interval').show()
$('#runNmbrTextfield').hide()
$('#partition-field').show()
$('#runInfo').hide()}else if($(this).val()=='Fill'){$('.history_interval').hide()
$('#runNmbrTextfield').show()
$('#partition-field').hide()
var ri=$('#runInfo')
ri[0].innerHTML='<span class="glyphicon glyphicon-info-sign"></span><span>Fill Information</span>'
ri[0].title='<b>Fill Information</b>'
$('#runInfo').show()}else{$('.history_interval').hide()
$('#runNmbrTextfield').show()
$('#partition-field').hide()
var ri=$('#runInfo')
ri[0].innerHTML='<span class="glyphicon glyphicon-info-sign"></span><span>Run Information</span>'
ri[0].title='<b>Run Information</b>'
$('#runInfo').show()}})
var current_type=Cookies.get('source-type-field')
if(current_type){$('#source-type-field').val(current_type).trigger('change')}
set_rundb_info()})
function is_alarm_folder(node_id){if(node_id)return node_id.indexOf('alarm-subsys-folder')==0}
function selectAlarmNode(e,data){if(!is_alarm_folder(data.node.id))
load_dashboard(data.node.original.histo_id,data.node.original.msg_id,undefined,undefined)}
function createAlarmJSTrees(jsonData){$('#alarmTree').jstree({core:{animation:1,data:jsonData.alarms}})
$('#alarmTree').bind('select_node.jstree',function(event,data){selectAlarmNode(event,data)})}
function load_alarms(){$.ajax({async:true,type:'GET',url:'/alarms',dataType:'json',success:function(json){createAlarmJSTrees(json)
$('#loadingAlarms').css('display','none')},error:function(xhr,ajaxOptions,thrownError){}})}
$(function(){load_alarms()})