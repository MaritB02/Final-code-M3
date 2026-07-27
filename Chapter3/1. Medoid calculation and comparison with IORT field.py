# RECURRENCE MEDOID VERSUS IORT FIELD
import slicer
import vtk
import numpy as np

# Settings
Segmentation_Name = "Segmentation"
IORT_Model_Name = "IORT Field"

recurrenceNames = ["recurrence1", "recurrence2", "recurrence3", "recurrence4"] # Change into the correct names

# Optionel: put limit for faster calculations
Max_Points = np.inf # optional, np.inf if you want to calculate for all points, 20000 in case of large tumours

# Get input data
segmentationNode = slicer.util.getNode(Segmentation_Name)
iortModelNode = slicer.util.getNode(IORT_Model_Name)

# Make sure binary labelmap exists
segmentationNode.CreateBinaryLabelmapRepresentation()

# Get IORT field polydata
iortPolyData = iortModelNode.GetPolyData()

# Prepare inside/outside tester for IORT field
insideTester = vtk.vtkSelectEnclosedPoints()
insideTester.SetSurfaceData(iortPolyData)
insideTester.SetTolerance(0.0001)
insideTester.Initialize(iortPolyData)

# Define helper functions
def get_segment_voxel_points_ras(segmentationNode, segmentId): # Returning all RAS coordinates of voxels of a segment

    labelmapNode = slicer.mrmlScene.AddNewNodeByClass(
        "vtkMRMLLabelMapVolumeNode",
        "temporary_labelmap"
    )

    segmentIds = vtk.vtkStringArray()
    segmentIds.InsertNextValue(segmentId)

    slicer.modules.segmentations.logic().ExportSegmentsToLabelmapNode(
        segmentationNode,
        segmentIds,
        labelmapNode
    )

    arr = slicer.util.arrayFromVolume(labelmapNode)
    kji = np.argwhere(arr > 0)

    ijkToRAS = vtk.vtkMatrix4x4()
    labelmapNode.GetIJKToRASMatrix(ijkToRAS)

    points = []

    for k, j, i in kji:
        ras = [0.0, 0.0, 0.0, 1.0]
        ijkToRAS.MultiplyPoint([i, j, k, 1.0], ras)
        points.append(ras[:3])

    slicer.mrmlScene.RemoveNode(labelmapNode)

    return np.array(points)

def compute_medoid(points):
    if len(points) > Max_Points:
        indices = np.random.choice(len(points), Max_Points, replace=False)
        pointsUsed = points[indices]
    else:
        pointsUsed = points

    bestIndex = None
    bestMeanDistance = np.inf

    for i in range(len(pointsUsed)):
        distances = np.linalg.norm(pointsUsed - pointsUsed[i], axis=1)
        meanDistance = np.mean(distances)

        if meanDistance < bestMeanDistance:
            bestMeanDistance = meanDistance
            bestIndex = i

    return pointsUsed[bestIndex], bestMeanDistance, len(points), len(pointsUsed)

# Calculate medoids
for recurrenceName in recurrenceNames:

    segmentId = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(
        recurrenceName
    )

    if not segmentId:
        print(f"Segment not found: {recurrenceName}")
        continue

    points = get_segment_voxel_points_ras(
        segmentationNode,
        segmentId
    )

    if len(points) == 0:
        print(f"No voxels found for {recurrenceName}")
        continue

    medoid, meanDistance, totalPoints, usedPoints = compute_medoid(points) # calculate medoid

    # Determine whether medoid is inside or outside IORT field
    isInside = insideTester.IsInsideSurface( 
        medoid[0],
        medoid[1],
        medoid[2]
    )

    result = "inside IORT" if isInside else "outside IORT"

    print(
        f"{recurrenceName}: {result}, "
        f"voxels used = {usedPoints}/{totalPoints}"
    )

    fiducialNode = slicer.mrmlScene.AddNewNodeByClass(
        "vtkMRMLMarkupsFiducialNode",
        f"{recurrenceName} medoid"
    )
    fiducialNode.AddControlPointWorld(medoid)

# Complete inside/outside test
insideTester.Complete()

