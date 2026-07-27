# IORT-PTV DISTANCE IN THE DIRECTION OF THE IORT FIELD NORMAL
import slicer
import vtk
import numpy as np

# Settings
sourceModelName = "IORT surface remeshed"
targetModelName = "PTVtot"
plane = slicer.util.getNode("P") 
rayLengthMm = 300.0 

# Define helper functions
def normalize(v): # normalize vector to length 1 (unit vector)
    v = np.array(v, dtype=float)
    n = np.linalg.norm(v)
    if n == 0:
        raise ValueError("Vector with length 0")
    return v / n

def create_line_markup(name, p1, p2, color=(1, 0, 0)): # draw distance line between two points
    lineNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsLineNode", name)
    lineNode.AddControlPoint(vtk.vtkVector3d(*p1))
    lineNode.AddControlPoint(vtk.vtkVector3d(*p2))

    displayNode = lineNode.GetDisplayNode()
    displayNode.SetSelectedColor(color)
    displayNode.SetColor(color)
    displayNode.SetLineThickness(0.3)
    displayNode.SetTextScale(3)

    return lineNode

# Get input data
sourceModel = slicer.util.getNode(sourceModelName)
targetModel = slicer.util.getNode(targetModelName)

sourcePoly = sourceModel.GetPolyData()
targetPoly = targetModel.GetPolyData()

if sourcePoly is None or sourcePoly.GetNumberOfPoints() == 0:
    raise ValueError("Source model does not contain valid polydata")

if targetPoly is None or targetPoly.GetNumberOfCells() == 0:
    raise ValueError("Target model does not contain valid polydata")

# Get IORT field normal
referenceNormal = [0.0, 0.0, 0.0] # as in previous script
plane.GetNormalWorld(referenceNormal)
referenceNormal = normalize(referenceNormal)

print("referenceNormal =", referenceNormal) 
print("Amount of source points =", sourcePoly.GetNumberOfPoints())

# Create locator for ray intersections with PTV surface
# Source: https://www.kitware.com/ray-casting-ray-tracing-with-vtk/
obbTree = vtk.vtkOBBTree()
obbTree.SetDataSet(targetPoly)
obbTree.BuildLocator()

# Collect source points from IORT surface
points = np.array([sourcePoly.GetPoint(i) for i in range(sourcePoly.GetNumberOfPoints())], dtype=float)

# Calculate distances, source: https://www.kitware.com/ray-casting-ray-tracing-with-vtk/
sourcePtsHit = [] # points on IORT surface
hitPts = [] # points on PTV
distances = [] # distances between both

for i, p in enumerate(points):
    p1 = np.array(p, dtype=float)
    p2 = p1 + referenceNormal * rayLengthMm

    intersectionPoints = vtk.vtkPoints()
    intersectionCellIds = vtk.vtkIdList()

    hit = obbTree.IntersectWithLine(p1, p2, intersectionPoints, intersectionCellIds)

    if hit and intersectionPoints.GetNumberOfPoints() > 0: # only rays that actually hit the PTV will be taken into account
        hp = np.array(intersectionPoints.GetPoint(0), dtype=float) # take the first intersection point
        d = float(np.linalg.norm(hp - p1))

        sourcePtsHit.append(p1)
        hitPts.append(hp)
        distances.append(d)

# Convert results to NumPy arrays
sourcePtsHit = np.array(sourcePtsHit)
hitPts = np.array(hitPts)
distances = np.array(distances)

# Calculate statistics
minIdx = int(np.argmin(distances))
maxIdx = int(np.argmax(distances))

medianDist = float(np.median(distances))
medianIdx = int(np.argmin(np.abs(distances - medianDist))) 

meanDist = float(np.mean(distances))
meanIdx = int(np.argmin(np.abs(distances - meanDist))) 

minDist = float(distances[minIdx])
maxDist = float(distances[maxIdx])
medianValue = float(distances[medianIdx]) # Actual measured distances of the lines displayed for the median
meanValue = float(distances[meanIdx]) # Actual measured distances of the lines displayed for the mean 
stdDist = float(np.std(distances))
q1 = float(np.percentile(distances, 25))
q3 = float(np.percentile(distances, 75))

# Print results
print(f"Amount of valid measurements: {len(distances)}")
print(f"Minimum: {minDist:.3f} mm")
print(f"Maximum: {maxDist:.3f} mm")
print(f"Mean: {meanDist:.3f} mm")
print(f"Displayed mean line distance: {meanValue:.3f} mm")
print(f"Median: {medianDist:.3f} mm")
print(f"Displayed median line distance: {medianValue:.3f} mm")
print(f"Std: {stdDist:.3f} mm")
print(f"IQR: {q1:.3f} - {q3:.3f} mm")

# Create table for results
tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", "Distances")

# Add columns
tableNode.AddColumn()
tableNode.GetTable().GetColumn(0).SetName("Metric")

tableNode.AddColumn()
tableNode.GetTable().GetColumn(1).SetName("Value (mm)")

# Fill table
table = tableNode.GetTable()
metrics = ["Minimum", "Maximum", "Mean", "Median", "Std", "q1", "q3"]
values = [minDist, maxDist, meanDist, medianDist, stdDist, q1, q3]
table.SetNumberOfRows(len(metrics))

for i in range(len(metrics)):
    table.SetValue(i, 0, metrics[i])
    table.SetValue(i, 1, f"{values[i]:.3f}")
    
# Create distance lines
create_line_markup(
    "Min",
    sourcePtsHit[minIdx],
    hitPts[minIdx],
    color=(1, 0, 0)   # red
)

create_line_markup(
    "Median",
    sourcePtsHit[medianIdx],
    hitPts[medianIdx],
    color=(1, 0, 0)   # red
)

create_line_markup(
    "Mean",
    sourcePtsHit[meanIdx],
    hitPts[meanIdx],
    color=(1, 0, 0)   # red
)

create_line_markup(
    "Max",
    sourcePtsHit[maxIdx],
    hitPts[maxIdx],
    color=(1, 0, 0)   # red
)

