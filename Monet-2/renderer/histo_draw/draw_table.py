###############################################################################
# (c) Copyright 2000-2020 CERN for the benefit of the LHCb Collaboration      #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################

from bokeh.models import ColumnDataSource, DataTable, TableColumn


def renderTable(
    histodb_hist,
    histo_data,
    draw_params,
    ref_data=None,
    highlight=None,
    motherplot=None,
    is_mother=False,
    extratext="",
):
    data = histo_data["data"]["key_data"]
    title = draw_params.get("showtitle", "") or data.get("title", "")
    to_print = "N/A"
    try:
        to_print = data["values"][-1][1]
    except Exception:
        pass

    if not motherplot:
        datas = {"Counter": [title], "Value": [to_print]}
        source = ColumnDataSource(datas)
        columns = [
            TableColumn(field="Counter", title="Counter"),
            TableColumn(field="Value", title="Value"),
        ]
        table = DataTable(source=source, columns=columns)
    else:
        new_datas = {"Counter": [title], "Value": [to_print]}
        motherplot.source.stream(new_datas)
        table = motherplot
    return table

def renderCountersTable(histodb_hist,
                histo_data,
                draw_params,
                ref_data=None,
                highlight=None,
                motherplot=None,
                is_mother=False,
                extratext=''):
    data = histo_data['data']['key_data']
    
    output_values = []
    output_labels = []
    
    values = data['values']
    labels = data['bin_labelsX']
    
    av_counter_original_name = {}
    av_counters_sum = {}
    av_counters_n_entries = {}
    
    for bin_value, counter_name in zip(values, labels):
        
        for required_counter in histodb_hist['counters']:
            if required_counter in counter_name:
                output_values += [bin_value]
                output_labels += [counter_name]
                
                break
                
        for required_counter in histodb_hist['averaging_counters']:
            if counter_name.endswith(f"{required_counter}_sum"):
                count = sum(1 for key in av_counters_sum if key.startswith(f"{required_counter}_"))
                unique_key = f"{required_counter}_{count + 1}" if count else required_counter
                
                av_counters_sum[unique_key] = bin_value
                av_counter_original_name[unique_key] = counter_name
                
                break

            elif counter_name.endswith(f"{required_counter}_n_entries"):
                count = sum(1 for key in av_counters_n_entries if key.startswith(f"{required_counter}_"))
                unique_key = f"{required_counter}_{count + 1}" if count else required_counter
                
                av_counters_n_entries[unique_key] = bin_value
                av_counter_original_name[unique_key] = counter_name
                
                break
            
            
            
    for counter_name in av_counter_original_name.keys():
        output_labels += [av_counter_original_name[counter_name]]
        output_values += [av_counters_sum[counter_name] / av_counters_n_entries[counter_name]]
        
    return_data = {'Counter' : output_labels,
                   "Value": output_values}
    
    if not motherplot:
        source = ColumnDataSource(return_data)
        columns = [ TableColumn(field='Counter', title='Counter') , 
                    TableColumn(field='Value', title='Value') ]
        table = DataTable( source = source, columns = columns )
    else:
        motherplot.source.stream( return_data )
        table = motherplot
    return table