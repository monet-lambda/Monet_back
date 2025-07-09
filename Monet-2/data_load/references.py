"""Functions to handle references"""
###############################################################################
# (c) Copyright 2000-2022 CERN for the benefit of the LHCb Collaboration      #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################

import logging
import os

import numpy as np
import ROOT
import yaml
from flask import jsonify, request
from flask.wrappers import Response

from presenter.blueprints._auth import requires_auth


@requires_auth
def update_references() -> Response:
    """Update reference files

    Returns:
        Response: HTML response with message
    """
    try:
        run_number = int(request.args.get("runnumber"))
    except ValueError:
        logging.error("Run number is not an integer")
        return jsonify({"success": False}), 404

    print("UPDATE REFERENCES")

    # Load the YAML configuration file
    try:
        with open("/home/gkhreich/trial/config.yaml", "r") as file:
            config = yaml.safe_load(file)
    except Exception as e:
        logging.error(f"Failed to load YAML configuration: {e}")
        return jsonify({"success": False, "error": "Configuration error"}), 500

    # Extract parameters from the YAML file
    scales = config["scales"]
    hist_titles = config["hist_titles"]
    inputs = config["inputs"]

    # Process each histogram individually
    for idx, input_item in enumerate(inputs):
        histo_name = input_item["name"]
        task_name = input_item["taskname"]
        print(run_number, histo_name, task_name)

        # Construct file path and open the ROOT file
        file_path = construct_path(run_number, task_name)
        root_file = ROOT.TFile.Open(file_path)

        if not root_file or root_file.IsZombie():
            logging.error(f"Could not open ROOT file: {file_path}")
            # Skip to the next histogram if the file could not be opened
            continue

        logging.info(f"Opened file: {file_path}")
        hist = root_file.Get(histo_name)

        if hist is None:
            logging.warning(
                f"Histogram '{histo_name}' not found in file for"
                " run number {run_number}. Skipping..."
            )
            continue  # Skip to the next histogram

        # Check if the retrieved object is a histogram
        if not isinstance(hist, (ROOT.TH1, ROOT.TH2)):
            logging.error(f"Object '{histo_name}' is not a histogram. Skipping...")
            continue  # Skip if it's not a histogram

        # Clone the histogram to avoid modifying the original
        hist_clone = hist.Clone()

        # Remove spaces from the histogram title
        cleaned_title = hist_titles[idx].replace(" ", "")
        hist_clone.SetTitle(cleaned_title)
        print(scales[idx])
        # Process the histogram, passing the corresponding scale
        processed_hist = process_histogram(hist_clone, run_number, scales[idx])
        print(f"Processed histogram: {processed_hist.GetName()}")

    return jsonify({"success": True})


def process_histogram(hist, run_number: int, scale: float):
    """Process histogram

    Args:
        hist (ROOT): ROOT histogram
        run_number (int): run number
        scale (float): scale factor

    Returns:
        ROOT: ROOT histogram
    """
    # Initialize reference values
    alpha = 0.2
    eps = 1e-10
    ref_array = np.zeros(5)  # Placeholder for the reference values
    suma_x0_ = 0  # Placeholder for suma_x0_
    # Check if the histogram is 2D
    if hist.InheritsFrom("TH2"):
        newbin_X = scale[0]
        newbin_Y = scale[1]
        NbinsX = hist.GetNbinsX()
        NbinsY = hist.GetNbinsY()
        rebin_factor_x = NbinsX // newbin_X
        rebin_factor_y = NbinsY // newbin_Y
        hist.Rebin2D(int(rebin_factor_x), int(rebin_factor_y))
        NbinsX = hist.GetNbinsX()
        NbinsY = hist.GetNbinsY()
        Nbins = NbinsX * NbinsY
    else:
        Nbins = hist.GetNbinsX()
        rebin_factor = Nbins // scale
        hist.Rebin(int(rebin_factor))

    # Process the histogram
    cached_run_numbers = []
    histo_name = hist.GetName()

    # Load reference data
    for fn in os.listdir("/home/gkhreich/trial/"):
        if f"reference_{histo_name}_" in fn and "suma" not in fn:
            rn = eval(fn.split("_")[-1][:-4])
            if rn < run_number:
                cached_run_numbers.append(rn)

    if cached_run_numbers != []:
        ref_rn = max(cached_run_numbers)
        ref_array = np.load(f"/home/gkhreich/trial/reference_{histo_name}_{ref_rn}.npy")
        suma_array = np.load(
            f"/home/gkhreich/trial/reference_{histo_name}_{ref_rn}_suma.npy"
        )
        x0_ = ref_array[0]
        e0_ = ref_array[1]

        ref_array_filename = (
            "/home/gkhreich/trial/reference_{histo_name}_{run_number}.npy"
        )
        np.save(ref_array_filename, ref_array)
        suma_filename = (
            "/home/gkhreich/trial/reference_{histo_name}_{run_number}_suma.npy"
        )
        np.save(suma_filename, suma_array)
    else:
        # Initialize 1D random array
        x0_ = np.random.poisson(100, size=(Nbins)).astype(np.float64)
        suma_x0_ = x0_.sum()
        x0_ = x0_ / suma_x0_  # normalize the reference to unity
        # poisson unc. on the reference
        sigma_x0_ = np.sqrt(x0_ / suma_x0_ - x0_**2 / suma_x0_)
        # initialize unc. for zero bins in the reference
        sigma_x0_[x0_ == 0] = 1 / suma_x0_

        omega = 1 / (sigma_x0_**2 + eps)
        W = (1 - alpha) * omega
        S_mu = (1 - alpha) * omega * x0_
        S_sigma = (1 - alpha) * omega * sigma_x0_**2
        x0_ = S_mu / W
        e0_ = np.sqrt(S_sigma / W)

        x0_filename = (
            f"/home/gkhreich/trial/reference_{hist.GetName()}_{run_number}.npy"
        )
        ref_array = np.array([x0_, e0_, W, S_mu, S_sigma])
        np.save(x0_filename, ref_array)

        suma_x0_filename = (
            f"/home/gkhreich/trial/reference_{hist.GetName()}_{run_number}_suma.npy"
        )
        suma_array = np.array([suma_x0_])
        np.save(suma_x0_filename, suma_array)

    del ref_array
    return hist


def construct_path(run_number: int, task_name: str) -> str:
    """Returns the path of the saveset histogram

    Args:
        run_number (int): run number
        task_name (str): name of the task

    Returns:
        str: path of the saveset histogram
    """
    range_number = (run_number // 10000) * 10000
    range_number2 = (run_number // 1000) * 1000
    return (
        f"/hist/Savesets/ByRun/{task_name}/{range_number}/{range_number2}/"
        "{task_name}-run{run_number}.root"
    )
