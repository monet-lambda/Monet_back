"""Utility library for handling histograms"""


import copy
import logging
import math
from typing import Any
from flask import current_app

import numpy
import ROOT

from interfaces.monitoringhub import monitoringhub_trend_loader, monitoringhub_counter_loader
from data_load.trend import MonetCounter, MonetTrend, MonetTrend2D

# Calo constants
BITSCOL     = 6
BITSROW     = 6
BITSAREA    = 2
SHIFTCOL    = 0
SHIFTROW    = SHIFTCOL + BITSCOL
SHIFTAREA   = SHIFTROW + BITSROW
MASKCOL  = ( ( 1 << BITSCOL ) - 1 ) << SHIFTCOL
MASKROW  = ( ( 1 << BITSROW ) - 1 ) << SHIFTROW
MASKAREA = ( ( 1 << BITSAREA ) - 1  ) << SHIFTAREA

NECELLS = 6016
NHCELLS = 1488

ECALcellIDs = [0] * 6016
HCALcellIDs = [0] * 1488

class Area:
    Outer = 0
    Middle = 1
    Inner = 2
    PinArea = 3

class CellCode:
    class Index:
        EcalCalo = 0
        HcalCalo = 1

class Constants:
    def __init__(self, calo, area, global_offset, id0, cols, rows):
        self.calo = calo
        self.area = area
        self.global_offset = global_offset
        self.id0 = id0
        self.cols = cols
        self.rows = rows

    def nCells(self):
        if self.area == Area.PinArea:
            return self.rows[0] * self.cols[0] + self.rows[2] * self.cols[2]
        else:
            return (self.rows[0] * (self.cols[0] + self.cols[1] + self.cols[2]) +
                    self.rows[1] * (self.cols[0] + self.cols[2]) +
                    self.rows[2] * (self.cols[0] + self.cols[1] + self.cols[2]))

    def offsetAfter(self):
        return self.global_offset + self.nCells()

constants = {(CellCode.Index.EcalCalo, Area.Outer): Constants(CellCode.Index.EcalCalo, Area.Outer, 0, [6, 0], [16, 32, 16], [16, 20, 16]),}
constants.update({(CellCode.Index.EcalCalo, Area.Middle): Constants(CellCode.Index.EcalCalo, Area.Middle, constants[(CellCode.Index.EcalCalo, Area.Outer)].offsetAfter(), [12, 0], [16, 32, 16], [8, 24, 8]),})
constants.update({(CellCode.Index.EcalCalo, Area.Inner): Constants(CellCode.Index.EcalCalo, Area.Inner, constants[(CellCode.Index.EcalCalo, Area.Middle)].offsetAfter(), [14, 8], [16, 16, 16], [12, 12, 12]),})
constants.update({(CellCode.Index.EcalCalo, Area.PinArea): Constants(CellCode.Index.EcalCalo, Area.PinArea, constants[(CellCode.Index.EcalCalo, Area.Inner)].offsetAfter(), [0, 0], [16, 32, 16], [4, 0, 4]),})
constants.update({(CellCode.Index.HcalCalo, Area.Outer): Constants(CellCode.Index.HcalCalo, Area.Outer, constants[(CellCode.Index.EcalCalo, Area.PinArea)].offsetAfter(), [3, 0], [8, 16, 8], [6, 14, 6]),})
constants.update({(CellCode.Index.HcalCalo, 1): Constants(CellCode.Index.HcalCalo, 1, constants[(CellCode.Index.HcalCalo, Area.Outer)].offsetAfter(), [2, 0], [14, 4, 14], [12, 4, 12]),})
constants.update({(CellCode.Index.HcalCalo, Area.PinArea): Constants(CellCode.Index.HcalCalo, Area.PinArea, constants[(CellCode.Index.HcalCalo, 1)].offsetAfter(), [0, 0], [16, 32, 16], [4, 0, 4]),})

def valid(calo, area, row, col):
    C = constants[(calo, area)]
    bound = [
        [C.id0[0], C.id0[0] + C.rows[0], C.id0[0] + C.rows[0] + C.rows[1], C.id0[0] + C.rows[0] + C.rows[1] + C.rows[2]],
        [C.id0[1], C.id0[1] + C.cols[0], C.id0[1] + C.cols[0] + C.cols[1], C.id0[1] + C.cols[0] + C.cols[1] + C.cols[2]]
    ]
    r = -1 if row < bound[0][0] else 0 if row < bound[0][1] else 1 if row < bound[0][2] else 2 if row < bound[0][3] else 3
    c = -1 if col < bound[1][0] else 0 if col < bound[1][1] else 1 if col < bound[1][2] else 2 if col < bound[1][3] else 3
    return r != -1 and r != 3 and c != -1 and c != 3 and not (r == 1 and c == 1)

def index(calo, area, row, col):
    C = constants[(calo, area)]
    strides = [C.cols[0] + C.cols[1] + C.cols[2], C.cols[0] + C.cols[2], C.cols[0] + C.cols[1] + C.cols[2]]
    offsets = [
        C.global_offset - C.id0[0] * strides[0] - C.id0[1],
        C.global_offset - C.id0[0] * strides[1] - C.id0[1] + C.rows[0] * C.cols[1],
        C.global_offset - C.id0[0] * strides[2] - C.id0[1] - C.rows[1] * C.cols[1]
    ]
    bound = [
        [C.id0[0] + C.rows[0], C.id0[0] + C.rows[0] + C.rows[1]],
        [C.id0[1] + C.cols[0], C.id0[1] + C.cols[0] + C.cols[1]]
    ]

    if area == Area.PinArea:
        off = (C.cols[0] + C.cols[1]) if (row >= C.rows[0] and col >= (C.cols[0] + C.cols[1])) else 0
        return C.global_offset + row * C.cols[0] + col - off
    else:
        r = 0 if row < bound[0][0] else 1 if row < bound[0][1] else 2
        return offsets[r] + row * strides[r] + col - (C.cols[1] if (r == 1 and col >= bound[1][1]) else 0)

for i in range(1,12000):
    cellID = i
    area = ( cellID & MASKAREA  ) >> SHIFTAREA
    col  = ( cellID & MASKCOL  ) >> SHIFTCOL
    row  = ( cellID & MASKROW  ) >> SHIFTROW
    if (index(0,area,row,col)<6016 and valid(0, area, row, col)):
        ECALcellIDs[index(0,area,row,col)]=cellID
    if (i<8000 and index(1,area,row,col)-6144<1488 and valid(1, area, row, col)):
            HCALcellIDs[index(1,area,row,col)-6144]=cellID


def iECAL2cellID(iECAL):
    if(iECAL>=0 and iECAL<NECELLS):
        return ECALcellIDs[iECAL]
    else:
        return 0

def iHCAL2cellID(iHCAL):
    if(iHCAL>=0 and iHCAL<NHCELLS):
        return HCALcellIDs[iHCAL]
    else:
        return 0

def try_get_object(f: ROOT.TFile, objname: str) -> ROOT.TObject:
    """Get ROOT object from file

    Args:
        f (ROOT.TFile): file
        objname (str): object name

    Returns:
        ROOT.TObject: ROOT object
    """
    objname = str(objname)
    o = f.Get(objname)

    return copy.deepcopy(o)


def get_key_from_root(
    f: ROOT.TFile,
    objname: str,
    scale_to_integral: float | None = None,
    scale_to_entries: float | None = None,
) -> dict[str, Any]:
    """Get object in dictionary format for Monet from a ROOT file

    Args:
        f (ROOT.TFile): ROOT file
        objname (str): name of the ROOT object
        scale_to_integral (float | None, optional): scale factor to integral. Defaults to None.
        scale_to_entries (float | None, optional): scale factor to number of entries. Defaults to None.

    Returns:
        dict[str, Any]: _description_
    """
    logging.debug("Getting `%s` from `%s`", objname, f)
    o = try_get_object(f, objname)

    return get_dict_from_object(
        o,
        objname=objname,
        scale_to_integral=scale_to_integral,
        scale_to_entries=scale_to_entries,
    )

def get_batch_from_file(filename, key_list, scale_dict=None):
    """get batch from file"""
    base_filename = filename.split("?", 1)[0]  # without URL args (e.g. EOS token)
    try:
        f = ROOT.TFile.Open(filename) if filename else ROOT.TFile()
        if f.IsZombie():
            return {
                key: {
                    "success": False,
                    "message": f"Could not load file `{base_filename}`",
                }
                for key, _, _ in key_list
            }
    except IOError as e:
        return {
            key: {"success": False, "message": str(e).replace(filename, base_filename)}
            for key, _, _ in key_list
        }

    ret = {}
    for key, task, options in key_list:
        assert isinstance(options, dict)
        norm = options.get("norm")
        ref_norm = options.get("ref")
        try:
            rootkey = key.split("/", 1)[1]
        except IndexError:
            return ret
        if norm:
            logging.debug("Normalizing to NORM=%s.", norm)
            ret[task + "/" + key] = get_key_from_root(
                f, rootkey, scale_to_integral=norm
            )
            continue

        if not scale_dict:
            logging.debug("Getting without normalization.")
            ret[task + "/" + key] = get_key_from_root(f, rootkey)
            continue

        if "TH2" in scale_dict[task + "/" + key]["data"]["key_class"]:
            continue  # do not load references for 2D-histograms

        scaling_kwargs = get_scaling_kwargs(task + "/" + key, ref_norm, scale_dict)
        ret[task + "/" + key] = get_key_from_root(f, rootkey, **scaling_kwargs)

    f.Close()
    return ret


def get_scaling_kwargs(key, ref_norm, scale_dict):
    """get arguments for reference scaling"""
    ret = {}
    try:
        if (
            (not ref_norm)
            or ref_norm == "AREA"
            and "integral" in scale_dict[key]["data"]["key_data"]
        ):
            data_integral = scale_dict[key]["data"]["key_data"]["integral"]
            ret["scale_to_integral"] = data_integral
        elif (
            ref_norm == "ENTR"
            and "numberEntries" in scale_dict[key]["data"]["key_data"]
        ):
            data_entries = scale_dict[key]["data"]["key_data"]["numberEntries"]
            ret["scale_to_entries"] = data_entries
    except IndexError:
        logging.info("Could not get scaling kwargs ")

    return ret



def get_dict_from_object(
    o: tuple[ROOT.TObject, str, str] | ROOT.TObject,
    objname: str = "",
    scale_to_integral: float | None = None,
    scale_to_entries: float | None = None,
    onlinehist: dict[str, Any] | None = None,
    profile: bool = False,
) -> dict[str, Any]:
    """Transform a ROOT object into a dictionary for Monet to display

    Args:
        o (tuple[ROOT.TObject, str, str] | ROOT.TObject): a ROOT object
        objname (str, optional): Name of the object. Defaults to "".
        scale_to_integral (float | None, optional): scale factor to integral. Defaults to None.
        scale_to_entries (float | None, optional): scale factor to number of entries. Defaults to None.
        onlinehist (dict[str, Any] | None, optional): dictionary of an online histogram. Defaults to None.
        profile (bool, optional): create profile histogram. Defaults to False.

    Returns:
        dict[str, Any]: online histogram in dictionary format
    """
    data = {}
    not_found = False
    json_name = None
    the_obj = o

    if isinstance(o, tuple):
        if len(o) == 3:
            data.update({"results": o[1]})
        json_name = o[-1]
        the_obj = o[0]

    if not the_obj:
        the_obj = ROOT.TH1F(objname, "** Not Found ** " + objname, 1, 0.0, 1.0)
        not_found = True

    classname = the_obj.ClassName()

    # If profile requested on a 2D histogram, transform the object here
    if profile in ["x", "y"]:
        if classname.startswith("TH2"):
            if profile == "x":
                the_obj = the_obj.ProfileX()
            else:
                the_obj = the_obj.ProfileY()
            classname = the_obj.ClassName()

    title = the_obj.GetTitle()
    if (not title) and onlinehist:
        try:
            title = onlinehist["name"]
        except KeyError:
            pass

    # Special CALO histograms
    if classname in set(["TProfile"]) and (onlinehist["display_options"].get("ecal_denseIndex", False) or onlinehist["display_options"].get("hcal_denseIndex", False)):
        isEcal = onlinehist["display_options"].get("ecal_denseIndex", False)
        calo2d = ROOT.TH2D("calo2d","calo2d",384 if isEcal else 64,-3878.4,3878.4,312 if isEcal else 52,-3151.2,3151.2)

        for i in range(0,NECELLS if isEcal else NHCELLS):
            cellID = iECAL2cellID(i) if isEcal else iHCAL2cellID(i)
            value = the_obj.GetBinContent(i+1)
            area = ( cellID & MASKAREA  ) >> SHIFTAREA
            col  = ( cellID & MASKCOL  ) >> SHIFTCOL
            row  = ( cellID & MASKROW  ) >> SHIFTROW
            m_det = 0 if isEcal else 1
            if not valid(m_det, area, row, col):
                continue

            for m in range(1,int(((6*1./(m_det*2+1))*1./(area+1))+1)):
                for n in range(int(((6*1./(m_det*2+1))*1./(area+1)))):

                    xbin = int((col+(32*1./(m_det+1))*area)*(6*1./(m_det*2+1))*1./(area+1)+m)
                    ybin = int((row+(32*1./(m_det+1))*area)*(6*1./(m_det*2+1))*1./(area+1)-(36*1./(m_det*5+1))+n+1)

                    if ( ( m_det==0 and ( (area==0 and not(xbin>=97 and ybin>=97 and xbin<=288 and ybin<=216) ) or
                                        (area==1 and (xbin>=97 and ybin>=97 and xbin<=288 and ybin<=216) or
                                        not(xbin>=145 and ybin>=121 and xbin<=240 and ybin<=192) ) or
                                        (area==2 and (xbin>=145 and ybin>=121 and xbin<=240 and ybin<=192) and
                                        not(xbin>=177 and ybin>=145 and xbin<=208 and ybin<=168) ) ) )
                        or ( m_det==1 and ( (area==0 and not(xbin>=17 and ybin>=13 and xbin<=48 and ybin<=40) ) or
                                            (area==1 and (xbin>=17 and ybin>=13 and xbin<=48 and ybin<=40) ) ) ) ):

                        calo2d.SetBinContent(xbin,ybin,value)
        the_obj = calo2d
        classname = the_obj.ClassName()
    elif classname in set(["TProfile"]) and (onlinehist["display_options"].get("ecal_index", False) or onlinehist["display_options"].get("hcal_index", False)):
        isEcal = onlinehist["display_options"].get("ecal_index", False)
        calo2d = ROOT.TH2D("calo2d","calo2d",384 if isEcal else 64,-3878.4,3878.4,312 if isEcal else 52,-3151.2,3151.2)

        for i in range(0,12000 if isEcal else 8000):
            cellID = i
            value = the_obj.GetBinContent(i+1)
            area = ( cellID & MASKAREA  ) >> SHIFTAREA
            col  = ( cellID & MASKCOL  ) >> SHIFTCOL
            row  = ( cellID & MASKROW  ) >> SHIFTROW
            m_det = 0 if isEcal else 1
            if not valid(m_det, area, row, col):
                continue

            for m in range(1,int(((6*1./(m_det*2+1))*1./(area+1))+1)):
                for n in range(int(((6*1./(m_det*2+1))*1./(area+1)))):

                    xbin = int((col+(32*1./(m_det+1))*area)*(6*1./(m_det*2+1))*1./(area+1)+m)
                    ybin = int((row+(32*1./(m_det+1))*area)*(6*1./(m_det*2+1))*1./(area+1)-(36*1./(m_det*5+1))+n+1)

                    if ( ( m_det==0 and ( (area==0 and not(xbin>=97 and ybin>=97 and xbin<=288 and ybin<=216) ) or
                                        (area==1 and (xbin>=97 and ybin>=97 and xbin<=288 and ybin<=216) or
                                        not(xbin>=145 and ybin>=121 and xbin<=240 and ybin<=192) ) or
                                        (area==2 and (xbin>=145 and ybin>=121 and xbin<=240 and ybin<=192) and
                                        not(xbin>=177 and ybin>=145 and xbin<=208 and ybin<=168) ) ) )
                        or ( m_det==1 and ( (area==0 and not(xbin>=17 and ybin>=13 and xbin<=48 and ybin<=40) ) or
                                            (area==1 and (xbin>=17 and ybin>=13 and xbin<=48 and ybin<=40) ) ) ) ):

                        calo2d.SetBinContent(xbin,ybin,value)
        the_obj = calo2d
        classname = the_obj.ClassName()


    if classname in set(["TH1D", "TProfile", "TH1F"]):
        if scale_to_integral and the_obj.GetSumOfWeights():
            the_obj.Scale(scale_to_integral / the_obj.GetSumOfWeights())
        elif scale_to_entries and the_obj.GetEntries():
            the_obj.Scale(scale_to_entries / the_obj.GetEntries())

        xaxis, yaxis = the_obj.GetXaxis(), the_obj.GetYaxis()
        nbins = xaxis.GetNbins()

        values, binning, uncertainties, bin_labels = [], [], [], []
        for i in range(1, nbins + 1):
            values.append(the_obj.GetBinContent(i))
            binning.append((xaxis.GetBinLowEdge(i), xaxis.GetBinUpEdge(i)))
            uncertainties.append((the_obj.GetBinErrorLow(i), the_obj.GetBinErrorUp(i)))
            bin_labels.append(xaxis.GetBinLabel(i))
        val_kurtosis, val_kurosis_error = round_to_2e(
            the_obj.GetKurtosis(), the_obj.GetKurtosis(11)
        )
        val_skewness, val_skewness_error = round_to_2e(
            the_obj.GetSkewness(), the_obj.GetSkewness(11)
        )
        val_rms, val_rms_error = round_to_2e(the_obj.GetRMS(), the_obj.GetRMSError())
        val_mean, val_mean_error = round_to_2e(
            the_obj.GetMean(), the_obj.GetMeanError()
        )

        data.update(
            {
                "type": classname[1:],
                "kurtosis": val_kurtosis,
                "kurtosis_error": val_kurosis_error,
                "skewness": val_skewness,
                "skewness_error": val_skewness_error,
                "integral": the_obj.GetSumOfWeights(),
                "integral_width": the_obj.Integral("width"),
                "underflow": the_obj.GetBinContent(0),
                "overflow": the_obj.GetBinContent(nbins + 1),
                "RMS": val_rms,
                "RMS_error": val_rms_error,
                "mean": val_mean,
                "mean_error": val_mean_error,
                "numberEntries": the_obj.GetEntries(),
                "title": title,
                "nbins": nbins,
                "axis_titles": (xaxis.GetTitle(), yaxis.GetTitle()),
                "values": values,
                "binning": binning,
                "uncertainties": uncertainties,
                "bin_labelsX": bin_labels,
            }
        )
    elif classname in set(["TGraph", "TGraphErrors"]):
        xaxis, yaxis = the_obj.GetXaxis(), the_obj.GetYaxis()
        data.update(
            {
                "type": classname[1:],
                "numberEntries": the_obj.GetN(),
                "title": title,
                "nbins": the_obj.GetN(),
                "axis_titles": (xaxis.GetTitle(), yaxis.GetTitle()),
                "values": [the_obj.GetPointY(i) for i in range(the_obj.GetN())],
                "uncertainties": [
                    (the_obj.GetErrorYlow(i), the_obj.GetErrorYhigh(i))
                    for i in range(the_obj.GetN())
                ],
                "bin_labelsX": [xaxis.GetBinLabel(i) for i in range(the_obj.GetN())],
                "bin_labelsY": [yaxis.GetBinLabel(i) for i in range(the_obj.GetN())],
                "binning": [
                    (
                        the_obj.GetPointX(i) - the_obj.GetErrorYlow(i),
                        the_obj.GetPointX(i) + the_obj.GetErrorXhigh(i),
                    )
                    for i in range(the_obj.GetN())
                ],
            }
        )
    elif classname in set(["TH2D", "TH2F", "TProfile2D"]):
        if classname == "TProfile2D":
            h_check = ROOT.gROOT.FindObject(the_obj.GetName() + "_pxy")
            if h_check:
                h_check.Delete()
            the_obj = the_obj.ProjectionXY()

        xaxis, yaxis, zaxis = the_obj.GetXaxis(), the_obj.GetYaxis(), the_obj.GetZaxis()
        nbins_x, nbins_y = xaxis.GetNbins(), yaxis.GetNbins()
        nbins = nbins_x * nbins_y
        values, uncertainties = [], []
        o_array = the_obj.GetArray()
        if classname in ("TH2D", "TProfile2D"):
            values_ = numpy.ndarray(
                ((nbins_x + 2) * (nbins_y + 2),), dtype=numpy.float64, buffer=o_array
            )
        else:
            values_ = numpy.ndarray(
                ((nbins_x + 2) * (nbins_y + 2),), dtype=numpy.float32, buffer=o_array
            )

        values_ = numpy.transpose(
            values_.reshape((nbins_y + 2, nbins_x + 2), order="C"), (1, 0)
        )
        values = (values_[1:-1, 1:-1]).copy()
        binning_x = numpy.array(
            [
                (xaxis.GetBinLowEdge(i), xaxis.GetBinUpEdge(i))
                for i in range(1, nbins_x + 1)
            ]
        )
        binning_y = numpy.array(
            [
                (yaxis.GetBinLowEdge(i), yaxis.GetBinUpEdge(i))
                for i in range(1, nbins_y + 1)
            ]
        )

        labelsx, labelsy = [], []
        if onlinehist:
            labelsx = [
                onlinehist["binlabel"][i]
                for i in range(onlinehist.get("nxbinlabels", 0))
            ]
            labelsy = [
                onlinehist["binlabel"][i]
                for i in range(
                    onlinehist.get("nxbinlabels", 0),
                    onlinehist.get("nxbinlabels", 0) + onlinehist.get("nybinlabels", 0),
                )
            ]

        if len(labelsx) == 0:
            labelsx = [xaxis.GetBinLabel(i) for i in range(1, nbins_x + 1)]

        if len(labelsy) == 0:
            labelsy = [yaxis.GetBinLabel(i) for i in range(1, nbins_y + 1)]

        data.update(
            {
                "type": classname[1:],
                "numberEntries": the_obj.GetEntries(),
                "integral": the_obj.Integral(),
                "mean_x": round(the_obj.GetMean(1), 3),
                "RMS_x": round(the_obj.GetRMS(1), 3),
                "mean_y": round(the_obj.GetMean(2), 3),
                "RMS_y": round(the_obj.GetRMS(2), 3),
                "title": title,
                "nbins": nbins,
                "xnbins": nbins_x,
                "ynbins": nbins_y,
                "axis_titles": (xaxis.GetTitle(), yaxis.GetTitle(), zaxis.GetTitle()),
                "values": values,
                "xbinning": binning_x,
                "ybinning": binning_y,
                "uncertainties": uncertainties,
                "bin_labelsX": labelsx,
                "bin_labelsY": labelsy,
            }
        )
        del o_array
        del values_
    elif classname == "TEfficiency":
        # Set statistics option to kFNormal ( = 1 )
        the_obj.SetStatisticOption(1)
        eff_histo = the_obj.GetPassedHistogram()
        xaxis = eff_histo.GetXaxis()
        nbins = xaxis.GetNbins()
        values, binning, uncertainties = [], [], []
        for i in range(1, nbins + 1):
            values.append(the_obj.GetEfficiency(i))
            binning.append((xaxis.GetBinLowEdge(i), xaxis.GetBinUpEdge(i)))
            uncertainties.append(
                (the_obj.GetEfficiencyErrorLow(i), the_obj.GetEfficiencyErrorUp(i))
            )
        data.update(
            {
                "type": "Profile",
                "numberEntries": 1,
                "integral": 1,
                "mean": 1,
                "RMS": 1,
                "title": "1",
                "nbins": nbins,
                "axis_titles": ("", "Efficiency"),
                "values": values,
                "binning": binning,
                "uncertainties": uncertainties,
            }
        )
    elif classname == "MonetTrend":
        data.update(
            {
                "type": "Trend",
                "title": title,
                "values": the_obj.data,
                "start_time": the_obj.start_time,
                "end_time": the_obj.end_time,
                "axis_titles": ("Time", "Rate"),
                "binning": [],
                "uncertainties": [],
            }
        )
    elif classname == "MonetTrend2D":
        data.update(
            {
                "type": "Trend2D",
                "title": title,
                "values": the_obj.data,
                "start_time": the_obj.start_time,
                "end_time": the_obj.end_time,
                "axis_titles": (
                    onlinehist["name"].split("%")[0].rstrip(),
                    onlinehist["name"].split("%")[1].lstrip(),
                ),
                "binning": [],
                "uncertainties": [],
            }
        )
    elif classname == "MonetCounter":
        try:
            data.update(
                {
                    "type": "Counter",
                    "title": title,
                    "values": [(the_obj.data[0][0], the_obj.data[0][1])],
                    "start_time": the_obj.time,
                    "end_time": the_obj.time,
                    "axis_titles": ("Time", "Rate"),
                    "binning": [],
                    "uncertainties": [],
                }
            )
        except IndexError:
            data.update(
                {
                    "type": "Trend",
                    "title": title + " not found",
                    "values": [],
                    "start_time": the_obj.time,
                    "end_time": the_obj.time,
                    "axis_titles": ("Time", "Rate"),
                    "binning": [],
                    "uncertainties": [],
                }
            )
    else:
        data = {"error": "Unknown class"}

    return {
        "success": True,
        "data": {
            "key_class": classname,
            "key_title": the_obj.GetTitle(),
            "keyname": the_obj.GetName(),
            "key_data": data,
        },
        "not_found": not_found,
        "json_name": json_name,
    }


def round_to_2e(x: float, ex: float) -> tuple[float, float]:
    """Round number and error

    Args:
        x (float): number
        ex (float): error

    Returns:
        tuple[float,float]: rounded number and error
    """
    insanity = list(map(math.isnan, [x, ex])) + list(map(math.isinf, [x, ex]))
    if any(insanity) or x == 0:
        return 0, 0
    x_dig = -int(math.floor(math.log10(abs(x))))
    if ex != 0:
        ex_dig = -int(math.floor(math.log10(abs(ex))))
    else:
        ex_dig = x_dig
    return round(x, ex_dig), round(ex, ex_dig)

def get_rootobj(
    h, file_loader, time_range=None, ref=False, rundb_info=None, json_file=""
):
    """get ROOT object"""
    if "taskname" not in h.keys():
        raise RuntimeError("taskname not defined")

    if h["taskname"].startswith("WinCC/"):
        if time_range == (0, 0):
            return MonetTrend(data=[0, 0], start_time=0, end_time=1), "WinCC"
        if "%" in h["name"]:
            return MonetTrend2D(
                data=monitoringhub_trend_loader(
                    h,
                    start_time=time_range[0],
                    end_time=time_range[1],
                    hub_configuration=current_app.config.get("MONHUB_CONFIG", None),
                    wincc_server=current_app.config.get(
                        "WINCC_SERVER", "http://monitoringhub.lbdaq.cern.ch/v1"
                    ),
                    source="wincc",
                ),
                start_time=time_range[0],
                end_time=time_range[1],
            ), "WinCC"

        return MonetTrend(
            data=monitoringhub_trend_loader(
                h,
                start_time=time_range[0],
                end_time=time_range[1],
                hub_configuration=current_app.config.get("MONHUB_CONFIG", None),
                wincc_server=current_app.config.get(
                    "WINCC_SERVER", "http://monitoringhub.lbdaq.cern.ch/v1"
                ),
                source="wincc",
            ),
            start_time=time_range[0],
            end_time=time_range[1],
        ), "WinCC"
    elif h["taskname"].startswith("WinCCCounter/"):
        return MonetCounter(
            data=monitoringhub_counter_loader(
                h,
                start_time=time_range[0],
                end_time=time_range[1],
                hub_configuration=current_app.config.get("MONHUB_CONFIG", None),
                wincc_server=current_app.config.get(
                    "WINCC_SERVER", "http://monitoringhub.lbdaq.cern.ch/v1"
                ),
                source="wincc",
            ),
            time=time_range[1],
        ), "WinCC"
    elif h["taskname"].startswith("prometheus"):
        if time_range == (0, 0):
            return MonetTrend(data=[0, 0], start_time=0, end_time=1), "Prometheus"
        if "%" in h["name"]:
            return MonetTrend2D(
                data=monitoringhub_trend_loader(
                    h,
                    start_time=time_range[0],
                    end_time=time_range[1],
                    hub_configuration=current_app.config.get("MONHUB_CONFIG", None),
                    wincc_server=current_app.config.get(
                        "PROMETHEUS_SERVER", "http://10.128.97.74:9090/api/v1"
                    ),
                    source="prometheus",
                ),
                start_time=time_range[0],
                end_time=time_range[1],
            ), "Prometheus"

        return MonetTrend(
            data=monitoringhub_trend_loader(
                h,
                start_time=time_range[0],
                end_time=time_range[1],
                hub_configuration=current_app.config.get("MONHUB_CONFIG", None),
                wincc_server=current_app.config.get(
                    "PROMETHEUS_SERVER", "http://10.128.97.74:9090/api/v1"
                ),
                source="prometheus",
            ),
            start_time=time_range[0],
            end_time=time_range[1],
        ), "Prometheus"
    elif h["taskname"].startswith("CounterPrometheus"):
        return MonetCounter(
            data=monitoringhub_counter_loader(
                h,
                start_time=time_range[0],
                end_time=time_range[1],
                hub_configuration=current_app.config.get("MONHUB_CONFIG", None),
                wincc_server=current_app.config.get(
                    "PROMETHEUS_SERVER", "http://10.128.97.74:9090/api/v1"
                ),
                source="prometheusCounter",
            ),
            time=time_range[1],
        ), "Prometheus"

    else:
        return file_loader(h, json_file=json_file)
