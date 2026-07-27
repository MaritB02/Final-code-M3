import numpy as np
import slicer

# Settings
browserName = "Pointer Timeline"
proxyNodeName = "Pointer Transform"
gap_threshold = 5 # only breaks longer than 5 seconds are considered non-active

# Find browser node and proxy node
browserNode = slicer.util.getNode(browserName)
proxyNode = slicer.util.getNode(proxyNodeName)

# Get the sequence node that belongs to the proxy node 
seqNode = browserNode.GetSequenceNode(proxyNode)
if not seqNode:
    raise RuntimeError("No sequence node found for this proxy node")

# Read time stamps from sequence index values
t = []
for i in range(seqNode.GetNumberOfDataNodes()):
    v = seqNode.GetNthIndexValue(i)
    try:
        t.append(float(v))
    except ValueError:
        raise RuntimeError(f"Index value is not numeric")

t = np.array(t, dtype=float)

if len(t) < 2:
    raise RuntimeError("To little samples to calculate time")

# Calculate time differences between subsequent samples
dt = np.diff(t)

# Seperate active intervals and gaps
active_dt = dt[dt <= gap_threshold]
gap_dt = dt[dt > gap_threshold]

active_time = float(active_dt.sum())
gap_time = float(gap_dt.sum())
total_span = float(t[-1] - t[0]) # latest sample minus first sample

# Create active segments
segments = []
start = t[0]
for i, dti in enumerate(dt):
    if dti > gap_threshold:
        end = t[i]
        segments.append((start, end, end - start))
        start = t[i+1]
segments.append((start, t[-1], t[-1] - start)) # adding final segment as it has no gap after it

# Print results
print("Samples:", len(t))
print("t start/end:", t[0], t[-1], "sec")
print("Total span (t[-1]-t[0]):", total_span, "sec")
print("Gap threshold:", gap_threshold, "sec")
print("Active time:", active_time, "sec")
print("Active time:", active_time/60, "min")
print("Non-active time:", gap_time, "sec")
print("Non-active time:", gap_time/60, "min")
print("\nActive segments(start, end, duration):")
for s in segments:
    print(s)

