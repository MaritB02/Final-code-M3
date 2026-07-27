#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import slicer
import vtk
import numpy as np

# Settings
Seg_Node   = "Segmentation"
Seg_Name   = "US_bone"
CT_Model   = "bone" # 3D bone model
Ref_Vol    = "ultrasound.volume"
Sample_Step = 1 # 1 = all voxels

# Get the input data
segNode = slicer.util.getNode(Seg_Node)
ctModel = slicer.util.getNode(CT_Model)
refVol  = slicer.util.getNode(Ref_Vol)

seg = segNode.GetSegmentation()
segId = seg.GetSegmentIdBySegmentName(Seg_Name)

if not segId:
    raise RuntimeError(f"Segment '{Seg_Name}' not found.")

# Export US-bone segment to a temporary labelmap using the reference geometry 
lbl = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode", "tmp_lbl")
slicer.modules.segmentations.logic().ExportSegmentsToLabelmapNode(segNode, [segId], lbl, refVol)

# Convert labelmap to numpy array and create mask of US-bone voxels
arr = slicer.util.arrayFromVolume(lbl)  # shape [k, j, i]
mask = (arr > 0)
nvox = int(mask.sum())

if nvox == 0:
    slicer.mrmlScene.RemoveNode(lbl)
    raise RuntimeError("Labelmap is empty.")

# Get poly data of CT bone model
poly = ctModel.GetPolyData()
if poly is None or poly.GetNumberOfPoints() == 0:
    slicer.mrmlScene.RemoveNode(lbl)
    raise RuntimeError("CT model polydata is empty or CT_Model name is wrong.")

# Establish function for calculating distance
distFunc = vtk.vtkImplicitPolyDataDistance()
distFunc.SetInput(poly)

# Convert IJK to RAS
ijkToRas = vtk.vtkMatrix4x4()
lbl.GetIJKToRASMatrix(ijkToRas)

def ijk_to_ras(i, j, k, M):
    x = M.GetElement(0,0)*i + M.GetElement(0,1)*j + M.GetElement(0,2)*k + M.GetElement(0,3)
    y = M.GetElement(1,0)*i + M.GetElement(1,1)*j + M.GetElement(1,2)*k + M.GetElement(1,3)
    z = M.GetElement(2,0)*i + M.GetElement(2,1)*j + M.GetElement(2,2)*k + M.GetElement(2,3)
    return (x, y, z)

# Get voxel indices and optionally downsample
idx = np.argwhere(mask) # rows: [k, j, i]
idx = idx[::max(1, int(Sample_Step))]

# Compute distances (US-bone voxel center to CT-bone model surface)
dists = np.empty((idx.shape[0],), dtype=np.float32)
for n, (k, j, i) in enumerate(idx):
    ras = ijk_to_ras(int(i), int(j), int(k), ijkToRas)
    dists[n] = abs(distFunc.EvaluateFunction(ras)) 

# Calculate statistics 
mean_val   = float(dists.mean())
median_val = float(np.median(dists))
rms_val    = float(np.sqrt(np.mean(dists*dists)))
p95_val    = float(np.percentile(dists, 95))
max_val    = float(dists.max())
min_val    = float(dists.min())

results = [
    ("Mean", mean_val),
    ("Median", median_val),
    ("RMS", rms_val),
    ("95 percentile", p95_val),
    ("Max", max_val),
    ("Min", min_val),

]

# Create table for results
tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", "FRE_pointcloud")

# Add columns
tableNode.AddColumn()  
tableNode.GetTable().GetColumn(0).SetName("Metric")

tableNode.AddColumn()  
tableNode.GetTable().GetColumn(1).SetName("Value (mm)")

# Fill table
table = tableNode.GetTable()
table.SetNumberOfRows(len(results))

for row, (name, value) in enumerate(results):
    table.SetValue(row, 0, str(name))
    table.SetValue(row, 1, str(value))

# Print results   
print(f"Foreground voxels: {nvox} | sampled: {len(dists)} | step: {Sample_Step}")
print(f"Mean:   {float(dists.mean()):.2f} mm")
print(f"Median: {float(np.median(dists)):.2f} mm")
print(f"RMS:    {float(np.sqrt(np.mean(dists*dists))):.2f} mm")
print(f"95%:    {float(np.percentile(dists, 95)):.2f} mm")
print(f"Max:    {float(dists.max()):.2f} mm")
print(f"Min:    {float(dists.min()):.2f} mm")

# Remove temporary labelmap
slicer.mrmlScene.RemoveNode(lbl)

