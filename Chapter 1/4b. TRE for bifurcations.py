# TRE FOR BIFURCATIONS
import slicer
import math

# Settings
Fiducials_Node = "Landmarks"

# Define pairs: (Fiducial placed by radiologist, Landmark placed during surgery)
PAIRS = [
    ("Fiducial aorta bif", "Landmark aorta bif"),
    ("Fiducial aorta bif", "Landmark aorta bif rereg"),
    ("Fiducial aorta bif", "Landmark aorta bif MC"),
    ("Fiducial iliac bif l", "Landmark iliac bif l"),
    ("Fiducial iliac bif l", "Landmark iliac bif l rereg"),
    ("Fiducial iliac bif r", "Landmark iliac bif r"),
    ("Fiducial iliac bif r", "Landmark iliac bif r2"),
    ("Fiducial iliac bif r", "Landmark iliac bif r rereg"),
    ("Fiducial iliac bif r", "Landmark iliac bif r rereg2"),
    # ("Fiducial X", "Landmark X"),
]

# Distance line visualization
Plot_Lines = True
Line_Prefix = "Distance_"
Hide_Existing_With_Same_Name = True


# Define helper functions
def find_control_point_index_by_label(markupsNode, label):  # find the index of a control point based on its label
    for i in range(markupsNode.GetNumberOfControlPoints()):
        if markupsNode.GetNthControlPointLabel(i) == label:
            return i
    return None


def get_cp_world(markupsNode, index):  # get position of control point in world coordinates
    p = [0.0, 0.0, 0.0]
    markupsNode.GetNthControlPointPositionWorld(index, p)
    return p


def hide_nodes_with_name(nodeClassName, nameToHide):  # hide existing line with same name
    for node in slicer.util.getNodesByClass(nodeClassName):
        if node.GetName() == nameToHide:
            disp = node.GetDisplayNode()
            if disp:
                disp.SetVisibility(False)

def create_distance_line(p_start_world, p_end_world, lineName):  # draw distance line
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

# Find landmarks node
fiducialsNode = None

for node in slicer.util.getNodesByClass("vtkMRMLMarkupsFiducialNode"):
    if node.GetName() == Fiducials_Node:
        fiducialsNode = node
        break

# Create table for results
tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", "TRE_bifurcations")

# Add columns
tableNode.AddColumn()
tableNode.GetTable().GetColumn(0).SetName("FiducialNodeCT")

tableNode.AddColumn()
tableNode.GetTable().GetColumn(1).SetName("LandmarkPointer")

tableNode.AddColumn()
tableNode.GetTable().GetColumn(2).SetName("Distance_mm")

# Calculate distances
print("\nResults")

for fidName, landmarkLabel in PAIRS:

    # Searching fiducial node
    try:
        fidNode = slicer.util.getNode(fidName)
    except slicer.util.MRMLNodeNotFoundException:
        print(f"[SKIP] Fiducial node not found: '{fidName}'")
        continue

    if fidNode.GetNumberOfControlPoints() == 0:
        print(f"[SKIP] No control points in '{fidName}'")
        continue

    # Point A, get CT fiducial position in world coordinates
    pA = get_cp_world(fidNode, 0)

    # Find corresponding intraoperative landmark
    idx = find_control_point_index_by_label(fiducialsNode, landmarkLabel)

    if idx is None:
        print(f"[SKIP] Landmark label not found: '{landmarkLabel}'")
        continue

    # Point B, get intraoperative landmark position in world coordinates
    pB = get_cp_world(fiducialsNode, idx)

    # Calculate distance between corresponding points
    d = math.sqrt(
        (pA[0] - pB[0])**2 +
        (pA[1] - pB[1])**2 +
        (pA[2] - pB[2])**2
    )

    print(f"{fidName} to {landmarkLabel}: {d:.3f} mm")

    # Add results to table
    row = tableNode.AddEmptyRow()
    tableNode.SetCellText(row, 0, fidName)
    tableNode.SetCellText(row, 1, landmarkLabel)
    tableNode.SetCellText(row, 2, f"{d:.3f}")

    # Create distance line
    if Plot_Lines:
        safeFiducial = fidName.replace(" ", "_")
        safeLandmark = landmarkLabel.replace(" ", "_")
        lineName = f"{Line_Prefix}{safeFiducial}_to_{safeLandmark}"
        create_distance_line(pA, pB, lineName)
