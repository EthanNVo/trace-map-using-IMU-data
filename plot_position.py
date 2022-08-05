import matplotlib.pyplot as plt
import numpy as np
import io
import cv2

def twoD_trace_map(position):
  # creating an empty figure for plotting
  fig = plt.figure(figsize = (10, 10))

  ax = plt.axes()

  # defining a set of points for X,Y and Z
  x = position[:, 0]
  y = position[:, 1]
  z = position[:, 2]

  ax.plot(x, y, 'red')

  #Labelling title of map
  plt.title('2D Trace Map', fontweight='bold', size=15, y=1.05)

  #Labelling axes of map
  ax.set_xlabel('X-axis', fontweight ='bold')
  ax.set_ylabel('Y-axis', fontweight ='bold')

  #Labelling first/last points of map
  ax.text(x[0], y[0], "Beginning")
  ax.text(x[-1], y[-1], "End")

  # define a function which returns an image as numpy array from figure
  def get_img_from_fig(fig, dpi=180):
    buf = io.BytesIO()
    fig.savefig(buf, format="jpg", dpi=dpi)
    buf.seek(0)
    img_arr = np.frombuffer(buf.getvalue(), dtype=np.uint8)
    buf.close()
    img = cv2.imdecode(img_arr, 1)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img
  img = get_img_from_fig(fig)
  return img
