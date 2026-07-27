# DISTANCE RECURRENCE MEDOID TO IORT FIELD
# alternative: fiducial to model distance module
import slicer
import vtk
import math

# Nodes
IORT_Model_Name = "IORT Field"
recurrenceMedoids = ['recidief1 medoid', 'recidief2 medoid', 'recidief3 medoid', 'recidief4 medoid'] # Change into the correct names

# Distance line visualization
Plot_Lines = True
Line_Prefix = "Distance_"
Hide_Existing_With_Same_Name = True

# Get input data
iortModelNode = slicer.util.getNode(IORT_Model_Name)

# Define helper functions
def model_polydata_to_world(modelNode): # transforms model data to world coordinates (RAS) if a transform is applied to it
    poly = modelNode.GetPolyData()
    parentT = modelNode.GetParentTransformNode()
    if parentT is None:
        return poly

    t = vtk.vtkGeneralTransform()
    slicer.vtkMRMLTransformNode.GetTransformBetweenNodes(parentT, None, t)

    tf = vtk.vtkTransformPolyDataFilter()
    tf.SetTransform(t)
    tf.SetInputData(poly)
    tf.Update()
    return tf.GetOutput()

def build_locator(modelNode): # create vtkCellLocator that can find next point in model quickly
    polyWorld = model_polydata_to_world(modelNode)
    locator = vtk.vtkCellLocator()
    locator.SetDataSet(polyWorld)
    locator.BuildLocator()
    return locator

def get_cp_world(markupsNode, index): # get position of control point in world coordinates
    p = [0.0, 0.0, 0.0]
    markupsNode.GetNthControlPointPositionWorld(index, p)
    return p

def closest_distance(locator, p): # calculate distance to model surface and return closest point
    closest = [0.0, 0.0, 0.0]
    cellId = vtk.mutable(0)
    subId = vtk.mutable(0)
    dist2 = vtk.mutable(0.0)
    locator.FindClosestPoint(p, closest, cellId, subId, dist2)
    return math.sqrt(float(dist2)), closest

def hide_nodes_with_name(nodeClassName, nameToHide): # hide existing line with same name
    for n in slicer.util.getNodesByClass(nodeClassName):
        if n.GetName() == nameToHide:
            disp = n.GetDisplayNode()
            if disp:
                disp.SetVisibility(False)

def create_distance_line(p_start_world, p_end_world, lineName): # draw distance line
    if Hide_Existing_With_Same_Name:
        hide_nodes_with_name("vtkMRMLMarkupsLineNode", lineName)

    lineNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsLineNode", lineName)

    lineNode.AddControlPoint(p_start_world)
    lineNode.AddControlPoint(p_end_world)

    disp = lineNode.GetDisplayNode()
    if disp:
        disp.SetVisibility(True)
        try:
            disp.SetPropertiesLabelVisibility(True)  
        except Exception:
            pass
        try:
            disp.SetPointLabelsVisibility(False)    
        except Exception:
            pass

    return lineNode

def is_inside_model(modelNode, point): # determine whether point is inside model surface
    polyWorld = model_polydata_to_world(modelNode)

    points = vtk.vtkPoints()
    points.InsertNextPoint(point)

    pointPoly = vtk.vtkPolyData()
    pointPoly.SetPoints(points)

    enclosed = vtk.vtkSelectEnclosedPoints()
    enclosed.SetInputData(pointPoly)
    enclosed.SetSurfaceData(polyWorld)
    enclosed.Update()

    return enclosed.IsInside(0)

# Create table
tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", "Distance recurrence-IORT")

# Add columns
tableNode.AddColumn()
tableNode.GetTable().GetColumn(0).SetName("Recurrence")

tableNode.AddColumn()
tableNode.GetTable().GetColumn(1).SetName("Distance_mm")

# Calculate distances
# Create locator for IORT model
iortLocator = build_locator(iortModelNode)

print("\nResults")
    
for recurrenceMedoid in recurrenceMedoids:
    try:
        recurrenceNode = slicer.util.getNode(recurrenceMedoid)
    except slicer.util.MRMLNodeNotFoundException:
        print(f"{recurrenceMedoid}: not found")
        continue

    p = get_cp_world(recurrenceNode, 0) # Get recurrence medoid position in world coordinates
    dist_mm, closest = closest_distance(iortLocator, p) # Calculate shortest distance to IORT field surface

    if is_inside_model(iortModelNode, p):
        dist_mm = -dist_mm # Make distance negative when medoid is inside IORT field

    print(f"{recurrenceMedoid} to IORT field: {dist_mm:.3f} mm")

    # Add results to table
    row = tableNode.AddEmptyRow()
    tableNode.SetCellText(row, 0, recurrenceMedoid)
    tableNode.SetCellText(row, 1, f"{dist_mm:.3f}")

    # Create distance line
    if Plot_Lines:
        safeLabel = recurrenceMedoid.replace(" ", "_")
        safeModel = iortModelNode.GetName().replace(" ", "_")
        lineName = f"{Line_Prefix}{safeLabel}_to_{safeModel}"
        create_distance_line(p, closest, lineName)

