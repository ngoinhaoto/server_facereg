import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server_facereg.models.database import *  # Import all models from database.py
from sqlalchemy_schemadisplay import create_uml_graph
from sqlalchemy.orm import class_mapper

# Find all the mappers in the models
mappers = []
for attr in dir():
    if attr[0] == '_':  # Skip private attributes
        continue
    try:
        cls = globals()[attr]
        mappers.append(class_mapper(cls))
    except Exception:
        pass

# Generate the UML graph
graph = create_uml_graph(
    mappers,
    show_operations=False,  # Hide operations for simplicity
    show_multiplicity_one=False  # Hide multiplicity "1"
)

# Save the UML diagram as a PNG file
graph.write_png('uml_class_diagram.png')
print("UML class diagram saved as 'uml_class_diagram.png'")