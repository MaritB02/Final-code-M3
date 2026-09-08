# 3D Slicer Scripts

In this repository, a collection of Python scripts developed for data processing and analysis in 3D Slicer is presented as part of my Technical Medicine thesis on evaluating intraoperative electron radiotherapy (IOERT).

The scripts include tools for:

* Chapter 2: Calculation of pointer usage duration and registration errors.
* Chapter 3: Extraction of IOERT field surfaces and calculation of distances to the PTV.
* Chapter 4: Calculation of recurrence medoids, determination of whether these medoids are located inside or outside the IOERT field and PTV, and calculation of medoid-to-IOERT field distances.

## Usage

Scripts are intended to be run in the **Python Console in 3D Slicer**.

Before running a script, check the settings on top of the script and update model/segmentation/fiducial names, or other parameters if necessary, either in the 3D Slicer scene or the code.

## Requirements

* 3D Slicer
* Python Console within 3D Slicer
