import slicer
import vtk
import math
import numpy as np
 
# Settings
CT_Bone_Model = "bone" # CT bone model node
Create_CT_Closest_Markups = True # true = show computed CT closest points
CT_Closest_Markups_Name = "CT_closest_points"
 
# US landmark nodes, each should contain one control point
US_Nodes = [
    # Ilium left
    "IliumL1", "IliumL2", "IliumL3", "IliumL4", "IliumL5",
    # Ilium right
    "IliumR1", "IliumR2", "IliumR3", "IliumR4", "IliumR5",
    # Sacrum
    "Sacrum1", "Sacrum2", "Sacrum3", "Sacrum4", "Sacrum5",
    # Pubis
    "Pubis1", "Pubis2", "Pubis3", "Pubis4", "Pubis5",
]
 
# Find CT bone model
ctModel = slicer.util.getNode(CT_Bone_Model)

# Get poly data of CT bone model
poly = ctModel.GetPolyData()
if poly is None or poly.GetNumberOfPoints() == 0:
    raise RuntimeError("CT bone model polydata is empty or CT_Bone_Model name is wrong.")
    
# Create locator for finding the closest point on the CT bone surface 
locator = vtk.vtkCellLocator()
locator.SetDataSet(poly)
locator.BuildLocator()
 
# Create CT closest point markups
ctClosestNode = None

if Create_CT_Closest_Markups:
    try:
        old = slicer.util.getNode(CT_Closest_Markups_Name)
        slicer.mrmlScene.RemoveNode(old) # Remove existing node with the same name
    except:
        pass
 
    ctClosestNode = slicer.mrmlScene.AddNewNodeByClass(
        "vtkMRMLMarkupsFiducialNode", CT_Closest_Markups_Name
    )
    disp = ctClosestNode.GetDisplayNode()
    disp.SetTextScale(0.0)
    disp.SetVisibility3D(True)

# Calculate distances
allDistances = []
usedNames = []
 
# Variables used by VTK to return closest point information
closestPoint = [0.0, 0.0, 0.0]
cellId = vtk.reference(0)
subId = vtk.reference(0)
dist2 = vtk.reference(0.0)
 
for nameUS in US_Nodes:
    try:
        nodeUS = slicer.util.getNode(nameUS) # Find US landmark node
    except slicer.util.MRMLNodeNotFoundException:
        print(f"Node not found: {nameUS}")
        continue
 
    if nodeUS.GetNumberOfControlPoints() == 0: # Check that the node contains a control point
        print(f"No control points in: {nameUS}")
        continue
        
    # Get first US landmark point in world (RAS) coordinates
    pUS = [0.0, 0.0, 0.0]
    nodeUS.GetNthControlPointPositionWorld(0, pUS)
 
    # Find closest point on CT bone surface
    locator.FindClosestPoint(pUS, closestPoint, cellId, subId, dist2)
    d = math.sqrt(float(dist2)) # Squared distance to distance (mm)
 
    allDistances.append(d)
    usedNames.append(nameUS)
 
    # Add closest CT point to markup node for visualization
    if ctClosestNode is not None:
        ctClosestNode.AddControlPoint([closestPoint[0], closestPoint[1], closestPoint[2]])
        
# Calculate statistics  
dists = np.array(allDistances, dtype=np.float64)
if dists.size == 0:
    raise RuntimeError("No distances computed. Check US node names and that they contain points.")

mean_val = float(dists.mean())
median_val = float(np.median(dists))
rms_val = float(np.sqrt(np.mean(dists * dists)))
p95_val = float(np.percentile(dists, 95))
max_val = float(dists.max())
min_val = float(dists.min())

results = [
    ("Number of distances", len(dists)),
    ("Mean", mean_val),
    ("Median", median_val),
    ("RMS", rms_val),
    ("95 percentile", p95_val),
    ("Max", max_val),
    ("Min", min_val),
 
] 
 
# Create table for results
tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", "BRE")
 
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
print(f"N: {len(dists)}")
print(f"Mean: {mean_val:.3f} mm")
print(f"Median: {median_val:.3f} mm")
print(f"RMS: {rms_val:.3f} mm")
print(f"95%: {p95_val:.3f} mm")
print(f"Max: {max_val:.3f} mm")
print(f"Min: {min_val:.3f} mm")

