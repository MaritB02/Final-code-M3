import slicer
import vtk
import numpy as np

# Settings
inputModelName = "IORT Field"
outputModelName = "IORT surface"

# Define helper functions
def normalize(v): # normalize vector to length 1 (unit vector)
    v = np.array(v, dtype=float)
    n = np.linalg.norm(v)
    if n == 0:
        raise ValueError("Vector with length 0")
    return v / n 

# Get reference normal of plane
plane = slicer.util.getNode("P") 
referenceNormal = [0.0, 0.0, 0.0]
plane.GetNormalWorld(referenceNormal)
referenceNormal = normalize(referenceNormal)

print("Normal of reference plane:", referenceNormal)

# Tolerance in degrees (since normal of each face of surface may slightly differ)
angleToleranceDeg = 1.0

# Get input model
modelNode = slicer.util.getNode(inputModelName)
polyData = modelNode.GetPolyData()

# Calculate angle threshold
cosThreshold = np.cos(np.deg2rad(angleToleranceDeg)) # dot product = cos(angle)

# Calculate cell normals
normalsFilter = vtk.vtkPolyDataNormals()
normalsFilter.SetInputData(polyData)
normalsFilter.ComputePointNormalsOff()
normalsFilter.ComputeCellNormalsOn()
normalsFilter.SplittingOff()
normalsFilter.ConsistencyOn()
normalsFilter.AutoOrientNormalsOn()
normalsFilter.Update()

polyWithNormals = normalsFilter.GetOutput()
cellNormals = polyWithNormals.GetCellData().GetNormals()

# Select cells based on cell normal
selectedCellIds = vtk.vtkIdTypeArray()

for cellId in range(polyWithNormals.GetNumberOfCells()):
    n = np.array(cellNormals.GetTuple(cellId), dtype=float)
    n = normalize(n)
    dot = np.dot(n, referenceNormal)

    if dot >= cosThreshold:
        selectedCellIds.InsertNextValue(cellId)

print(f"Selected cells: {selectedCellIds.GetNumberOfTuples()}")

# Extract selected cells
selectionNode = vtk.vtkSelectionNode()
selectionNode.SetFieldType(vtk.vtkSelectionNode.CELL)
selectionNode.SetContentType(vtk.vtkSelectionNode.INDICES)
selectionNode.SetSelectionList(selectedCellIds)

selection = vtk.vtkSelection()
selection.AddNode(selectionNode)

extractSelection = vtk.vtkExtractSelection()
extractSelection.SetInputData(0, polyWithNormals)
extractSelection.SetInputData(1, selection)
extractSelection.Update()

# Convert extracted cells back to polydata
geometryFilter = vtk.vtkGeometryFilter()
geometryFilter.SetInputData(extractSelection.GetOutput())
geometryFilter.Update()

selectedPolyData = geometryFilter.GetOutput()

# Create output model
try:
    outputNode = slicer.util.getNode(outputModelName)
    outputNode.SetAndObservePolyData(selectedPolyData)
except slicer.util.MRMLNodeNotFoundException:
    outputNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", outputModelName)
    outputNode.SetAndObservePolyData(selectedPolyData)
    displayNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelDisplayNode")
    slicer.mrmlScene.AddNode(displayNode)
    outputNode.SetAndObserveDisplayNodeID(displayNode.GetID())

outputNode.CreateDefaultDisplayNodes()
outputNode.GetDisplayNode().SetVisibility(True)

