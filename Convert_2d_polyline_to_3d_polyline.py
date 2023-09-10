# Copyright (c) 2022 Juha Toivola
# Licensed under the terms of the MIT License

import arcpy
import os
from datetime import datetime
import re

class Convert2DPolylineTo3DPolylineException(Exception):
    error_msg = ""
    def __init__(self, error_msg, *args):
        super().__init__(args)
        self.error_msg = error_msg
    def __str__(self):
        return 'Exception: ' + self.error_msg
		
# This is used to execute code if the file was run but not imported
if __name__ == '__main__':
    polyline = arcpy.GetParameterAsText(0)
    elevation = arcpy.GetParameterAsText(1)
    output_fc = arcpy.GetParameterAsText(2)
    count_polyline = int(arcpy.GetCount_management(polyline).getOutput(0))
    if count_polyline == 0:
        raise Convert2DPolylineTo3DPolylineException("Input polyline feature class has no records")
    if count_polyline > 1:
        raise Convert2DPolylineTo3DPolylineException("Input polyline feature class must have only one record")
    desc = arcpy.Describe(polyline)
    spatial_ref = arcpy.Describe(polyline).spatialReference
    arcpy.env.outputCoordinateSystem = spatial_ref
    if desc.hasZ:
        raise Convert2DPolylineTo3DPolylineException("Input polyline feature already has an elevation field")
    # get python file's current directory
    project_dir = os.path.dirname(os.path.realpath(__file__))
    # create output gdb with unique name
    now = datetime.now()
    now_str = now.strftime("%d%b%Y_%H%M%S")
    tmp_pnt = "memory/tmp_pnt_" + now_str
    cell_x_size = arcpy.management.GetRasterProperties(elevation, "CELLSIZEX").getOutput(0)
    cell_y_size = arcpy.management.GetRasterProperties(elevation, "CELLSIZEY").getOutput(0)
    mean_cell_size = (int(cell_x_size) + int(cell_y_size)) / 2
    arcpy.management.GeneratePointsAlongLines(polyline, tmp_pnt, "DISTANCE", Distance="{0} Meters".format(mean_cell_size), Include_End_Points="END_POINTS")
    arcpy.ddd.AddSurfaceInformation(tmp_pnt, elevation, "Z")
    tmp_pnt_elev = "memory/tmp_pnt_elev_" + now_str
    arcpy.FeatureTo3DByAttribute_3d(tmp_pnt, tmp_pnt_elev, 'Z')
    tmp_txt = project_dir + "/tmp_txt_" + now_str + ".txt"
    arcpy.ddd.FeatureClassZToASCII(tmp_pnt_elev, project_dir, tmp_txt, "XYZ", delimiter="COMMA", decimal_separator="DECIMAL_POINT")
    output_polyline_feature_3d = output_fc
    arcpy.ddd.ASCII3DToFeatureClass(tmp_txt, "XYZ", output_polyline_feature_3d, "POLYLINE")
    # remove tmp txt file
    os.chdir(project_dir)
    os.remove(tmp_txt)
    # delete tmp memory feature classes
    arcpy.management.Delete(tmp_pnt)
    arcpy.management.Delete(tmp_pnt_elev)
    # add to active map
    aprx = arcpy.mp.ArcGISProject('CURRENT')
    try:
        active_map = aprx.activeMap.name
        aprxMap = aprx.listMaps(active_map)[0]
        aprxMap.addDataFromPath(output_polyline_feature_3d)
    except:
        pass
