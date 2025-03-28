# your_mayavi_script.py
import sys
import json
import numpy as np
from mayavi import mlab

def main(params_path):
    # Load parameters
    with open(params_path) as f:
        params = json.load(f)
    
    # Load data
    data = np.load(params['data_path'])
    
    # Create visualization
    mlab.figure(size=(800, 600))
    src = mlab.pipeline.scalar_field(data)
    
    # Apply parameters
    mlab.pipeline.iso_surface(
        src, 
        contours=[params['iso_level']], 
        colormap=params['colormap']
    )
    
    mlab.axes()
    mlab.colorbar()
    mlab.show()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("Usage: python your_mayavi_script.py <params.json>")