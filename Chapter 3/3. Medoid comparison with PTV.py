# RECURRENCE MEDOID VERSUS PTV MODEL
import slicer
import vtk

# Settings
PTV_Model_Name = "PTV" # Transform PTV to model and make sure to harden transform!
medoidNames = ["recurrence1 medoid","recurrence2 medoid","recurrence3 medoid","recurrence4 medoid"] # Change into the correct names

# Get input data
ptvModelNode = slicer.util.getNode(PTV_Model_Name)
ptvPolyData = ptvModelNode.GetPolyData()

# Prepare inside/outside tester for PTV
insideTester = vtk.vtkSelectEnclosedPoints()
insideTester.SetSurfaceData(ptvPolyData)
insideTester.SetTolerance(0.0001)
insideTester.Initialize(ptvPolyData)

# Determine whether medoid is inside or outside PTV
print("\nResults")

for medoidName in medoidNames:

    try:
        medoidNode = slicer.util.getNode(medoidName)
    except slicer.util.MRMLNodeNotFoundException:
        print(f"{medoidName}: not found")
        continue

    p = [0.0, 0.0, 0.0]
    medoidNode.GetNthControlPointPositionWorld(0, p)

    isInside = insideTester.IsInsideSurface(
        p[0], 
        p[1], 
        p[2]
    )

    result = "inside PTV" if isInside else "outside PTV"

    print(f"{medoidName}: {result}")

# Complete inside/outside test
insideTester.Complete()

