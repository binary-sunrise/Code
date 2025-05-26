
# import os
# import geopandas as gpd
# from PIL import Image
# from PIL.ExifTags import TAGS, GPSTAGS
# import pandas as pd
# from shapely.geometry import Point
# import numpy as np
# from pathlib import Path
# from urllib.parse import urljoin
# from urllib.request import pathname2url


# class RoadImageLinker:
#     """
#     Links road polyline features to their closest geocoded images.
#     Each road feature gets associated with exactly one closest image.
#     """
    
#     def __init__(self, shapefile_path, images_folder):
#         """
#         Initialize the Road Image Linker
        
#         Args:
#             shapefile_path (str): Path to the road polylines shapefile
#             images_folder (str): Path to folder containing geocoded images
#         """
#         self.shapefile_path = Path(shapefile_path)
#         self.images_folder = Path(images_folder)
#         self.roads_gdf = None
#         self.image_points_gdf = None
#         self.supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}
        
#     def _convert_to_degrees(self, dms_value):
#         """
#         Convert GPS DMS (Degrees, Minutes, Seconds) to decimal degrees
        
#         Args:
#             dms_value: Tuple of (degrees, minutes, seconds)
            
#         Returns:
#             float: Decimal degrees
#         """
#         degrees, minutes, seconds = dms_value
#         return degrees + (minutes / 60.0) + (seconds / 3600.0)
    
#     def _path_to_uri(self, file_path):
#         """
#         Convert file path to URI format
        
#         Args:
#             file_path (str or Path): File system path
            
#         Returns:
#             str: URI formatted path (file:///C:/path/to/file.jpg)
#         """
#         abs_path = Path(file_path).resolve()
#         return urljoin('file:', pathname2url(str(abs_path)))
    
#     def extract_gps_from_image(self, image_path):
#         """
#         Extract GPS coordinates from image EXIF data
        
#         Args:
#             image_path (Path): Path to the image file
            
#         Returns:
#             tuple: (latitude, longitude) or (None, None) if no GPS data
#         """
#         try:
#             with Image.open(image_path) as image:
#                 exif_data = image._getexif()
                
#                 if exif_data is None:
#                     return None, None
                    
#                 # Extract GPS info
#                 gps_info = {}
#                 for tag, value in exif_data.items():
#                     decoded_tag = TAGS.get(tag, tag)
#                     if decoded_tag == "GPSInfo":
#                         for gps_tag in value:
#                             gps_decoded = GPSTAGS.get(gps_tag, gps_tag)
#                             gps_info[gps_decoded] = value[gps_tag]
                
#                 if not gps_info:
#                     return None, None
                
#                 # Extract and validate coordinates
#                 lat_ref = gps_info.get('GPSLatitudeRef')
#                 lat = gps_info.get('GPSLatitude')
#                 lon_ref = gps_info.get('GPSLongitudeRef')
#                 lon = gps_info.get('GPSLongitude')
                
#                 if not all([lat, lon, lat_ref, lon_ref]):
#                     return None, None
                
#                 # Convert to decimal degrees
#                 lat_decimal = self._convert_to_degrees(lat)
#                 lon_decimal = self._convert_to_degrees(lon)
                
#                 # Apply hemisphere corrections
#                 if lat_ref == 'S':
#                     lat_decimal = -lat_decimal
#                 if lon_ref == 'W':
#                     lon_decimal = -lon_decimal
                    
#                 return lat_decimal, lon_decimal
                
#         except Exception as e:
#             print(f"Warning: Could not extract GPS from {image_path.name}: {e}")
            
#         return None, None
    
#     def load_road_shapefile(self):
#         """
#         Load the road polylines shapefile
        
#         Returns:
#             bool: True if successful, False otherwise
#         """
#         try:
#             if not self.shapefile_path.exists():
#                 raise FileNotFoundError(f"Shapefile not found: {self.shapefile_path}")
                
#             self.roads_gdf = gpd.read_file(self.shapefile_path)
#             print(f"✓ Loaded {len(self.roads_gdf)} road features")
#             print(f"  CRS: {self.roads_gdf.crs}")
#             print(f"  Columns: {list(self.roads_gdf.columns)}")
            
#             return True
            
#         except Exception as e:
#             print(f"✗ Error loading shapefile: {e}")
#             return False
    
#     def extract_image_locations(self):
#         """
#         Extract GPS coordinates from all images in the folder
        
#         Returns:
#             bool: True if images with GPS found, False otherwise
#         """
#         if not self.images_folder.exists():
#             print(f"✗ Images folder not found: {self.images_folder}")
#             return False
            
#         print(f"Scanning for images in: {self.images_folder}")
        
#         image_data = []
#         total_images = 0
        
#         # Scan all image files
#         for image_file in self.images_folder.rglob('*'):
#             if image_file.suffix.lower() in self.supported_formats:
#                 total_images += 1
#                 lat, lon = self.extract_gps_from_image(image_file)
                
#                 if lat is not None and lon is not None:
#                     # Convert path to URI format
#                     uri_path = self._path_to_uri(image_file)
                    
#                     image_data.append({
#                         'image_path': str(image_file),
#                         'image_uri': uri_path,
#                         'filename': image_file.name,
#                         'latitude': lat,
#                         'longitude': lon,
#                         'geometry': Point(lon, lat)
#                     })
        
#         print(f"  Found {total_images} image files")
#         print(f"  {len(image_data)} images have GPS coordinates")
        
#         if image_data:
#             self.image_points_gdf = gpd.GeoDataFrame(image_data, crs='EPSG:4326')
#             self._print_coordinate_summary()
#             return True
#         else:
#             print("✗ No images with GPS data found")
#             return False
    
#     def _print_coordinate_summary(self):
#         """Print summary of coordinate ranges for debugging"""
#         if self.image_points_gdf is not None:
#             bounds = self.image_points_gdf.total_bounds
#             print(f"  Image coordinate bounds: [{bounds[0]:.6f}, {bounds[1]:.6f}] to [{bounds[2]:.6f}, {bounds[3]:.6f}]")
    
#     def reproject_data(self, target_crs='EPSG:3857'):
#         """
#         Reproject data to a projected CRS for accurate distance calculations
        
#         Args:
#             target_crs (str): Target coordinate reference system
#         """
#         print("Reprojecting data for distance calculations...")
        
#         # Reproject roads if geographic
#         if self.roads_gdf.crs.is_geographic:
#             self.roads_gdf = self.roads_gdf.to_crs(target_crs)
#             print(f"  Roads reprojected to {target_crs}")
            
#         # Reproject images to match roads
#         if self.image_points_gdf.crs != self.roads_gdf.crs:
#             self.image_points_gdf = self.image_points_gdf.to_crs(self.roads_gdf.crs)
#             print(f"  Images reprojected to {self.roads_gdf.crs}")
    
#     def find_closest_images_to_roads(self, max_distance=50):
#         """
#         Find the closest image for each road feature (one-to-one mapping)
        
#         Args:
#             max_distance (float): Maximum distance in meters to consider a match
            
#         Returns:
#             int: Number of successful matches
#         """
#         print(f"\nFinding closest images to roads (max distance: {max_distance}m)...")
        
#         # Add image columns if they don't exist
#         for col in ['Image_Path', 'Image_URI', 'Image_Name', 'Distance_m']:
#             if col not in self.roads_gdf.columns:
#                 self.roads_gdf[col] = ''
        
#         matches = []
        
#         # For each road, find its closest image
#         for road_idx, road_feature in self.roads_gdf.iterrows():
#             # Calculate distances from this road to all images
#             distances = self.image_points_gdf.geometry.distance(road_feature.geometry)
            
#             if len(distances) == 0:
#                 continue
                
#             min_distance = distances.min()
#             closest_image_idx = distances.idxmin()
            
#             # Only match if within maximum distance
#             if min_distance <= max_distance:
#                 closest_image = self.image_points_gdf.iloc[closest_image_idx]
                
#                 matches.append({
#                     'road_idx': road_idx,
#                     'image_idx': closest_image_idx,
#                     'distance': min_distance,
#                     'image_path': closest_image['image_path'],
#                     'image_uri': closest_image['image_uri'],
#                     'image_name': closest_image['filename']
#                 })
        
#         # Update roads with their closest images
#         matched_roads = 0
#         for match in matches:
#             road_idx = match['road_idx']
#             self.roads_gdf.at[road_idx, 'Image_Path'] = match['image_path']
#             self.roads_gdf.at[road_idx, 'Image_URI'] = match['image_uri']
#             self.roads_gdf.at[road_idx, 'Image_Name'] = match['image_name']
#             self.roads_gdf.at[road_idx, 'Distance_m'] = round(match['distance'], 2)
#             matched_roads += 1
        
#         print(f"✓ Matched {matched_roads} roads to their closest images")
        
#         # Print statistics
#         if matches:
#             distances = [m['distance'] for m in matches]
#             print(f"  Distance statistics:")
#             print(f"    Min: {min(distances):.1f}m")
#             print(f"    Max: {max(distances):.1f}m")
#             print(f"    Mean: {np.mean(distances):.1f}m")
#             print(f"    Median: {np.median(distances):.1f}m")
        
#         # Report unmatched roads
#         unmatched = len(self.roads_gdf) - matched_roads
#         if unmatched > 0:
#             print(f"  {unmatched} roads had no images within {max_distance}m")
        
#         return matched_roads
    
#     def save_updated_shapefile(self, output_path):
#         """
#         Save the updated shapefile with image associations
        
#         Args:
#             output_path (str): Path for output shapefile
            
#         Returns:
#             bool: True if successful, False otherwise
#         """
#         try:
#             output_path = Path(output_path)
#             output_path.parent.mkdir(parents=True, exist_ok=True)
            
#             # Convert back to geographic CRS for output
#             output_gdf = self.roads_gdf.to_crs('EPSG:4326')
#             output_gdf.to_file(output_path)
            
#             print(f"✓ Saved updated shapefile: {output_path}")
#             print(f"  Added columns: Image_Path, Image_URI, Image_Name, Distance_m")
            
#             return True
            
#         except Exception as e:
#             print(f"✗ Error saving shapefile: {e}")
#             return False
    
#     def create_qgis_assets(self, output_dir):
#         """
#         Create QGIS project template and HTML tooltip template
        
#         Args:
#             output_dir (str): Directory to save QGIS assets
#         """
#         output_dir = Path(output_dir)
#         output_dir.mkdir(parents=True, exist_ok=True)
        
#         # QGIS Project Template
#         project_template = '''<?xml version="1.0" encoding="UTF-8"?>
#                                 <qgis version="3.28" projectname="Road Crack Mapping">
#                                 <homePath path=""/>
#                                 <title>Road Crack Image Mapping</title>
#                                 <autotransaction active="0"/>
#                                 <evaluateDefaultValues active="0"/>
#                                 <trust active="0"/>
#                                 <projectCrs>
#                                     <spatialrefsys>
#                                     <wkt>GEOGCRS["WGS 84",DATUM["World Geodetic System 1984",ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],CS[ellipsoidal,2],AXIS["geodetic latitude (Lat)",north,ORDER[1],ANGLEUNIT["degree",0.0174532925199433]],AXIS["geodetic longitude (Lon)",east,ORDER[2],ANGLEUNIT["degree",0.0174532925199433]],USAGE[SCOPE["Horizontal component of 3D system."],AREA["World."],BBOX[-90,-180,90,180]],ID["EPSG",4326]]</wkt>
#                                     <proj4>+proj=longlat +datum=WGS84 +no_defs</proj4>
#                                     <srsid>3452</srsid>
#                                     <srid>4326</srid>
#                                     <authid>EPSG:4326</authid>
#                                     <description>WGS 84</description>
#                                     <projectionacronym>longlat</projectionacronym>
#                                     <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
#                                     <geographicflag>true</geographicflag>
#                                     </spatialrefsys>
#                                 </projectCrs>
#                                 </qgis>'''
        
#         project_file = output_dir / "road_image_mapping.qgs"
#         with open(project_file, 'w', encoding='utf-8') as f:
#             f.write(project_template)
        
#         # HTML Template for Map Tips (using URI format)
#         html_template = '''<!DOCTYPE html>
#                             <html>
#                             <head>
#                                 <style>
#                                     body { 
#                                         margin: 5px; 
#                                         font-family: Arial, sans-serif; 
#                                         background: #f9f9f9;
#                                         border-radius: 5px;
#                                         padding: 10px;
#                                     }
#                                     .header {
#                                         font-weight: bold;
#                                         color: #333;
#                                         margin-bottom: 10px;
#                                         border-bottom: 1px solid #ddd;
#                                         padding-bottom: 5px;
#                                     }
#                                     .image-container { 
#                                         text-align: center;
#                                         margin: 10px 0;
#                                     }
#                                     .road-image { 
#                                         max-width: 300px; 
#                                         max-height: 200px; 
#                                         border: 2px solid #007cba;
#                                         border-radius: 4px;
#                                         box-shadow: 0 2px 4px rgba(0,0,0,0.1);
#                                     }
#                                     .image-info {
#                                         font-size: 11px;
#                                         color: #666;
#                                         margin-top: 5px;
#                                         background: white;
#                                         padding: 5px;
#                                         border-radius: 3px;
#                                     }
#                                     .distance {
#                                         font-weight: bold;
#                                         color: #007cba;
#                                     }
#                                     .no-image {
#                                         color: #999;
#                                         font-style: italic;
#                                         text-align: center;
#                                         padding: 20px;
#                                     }
#                                 </style>
#                             </head>
#                             <body>
#                                 [% CASE WHEN "Image_URI" IS NOT NULL AND "Image_URI" != '' THEN %]
#                                     <div class="header">Road Crack Image</div>
#                                     <div class="image-container">
#                                         <img src="[% "Image_URI" %]" alt="Road crack image" class="road-image">
#                                         <div class="image-info">
#                                             <div><strong>File:</strong> [% "Image_Name" %]</div>
#                                             <div><strong>Distance:</strong> <span class="distance">[% "Distance_m" %]m</span></div>
#                                         </div>
#                                     </div>
#                                 [% ELSE %]
#                                     <div class="no-image">No image associated with this road segment</div>
#                                 [% END %]
#                             </body>
#                             </html>'''
        
#         html_file = output_dir / "image_tooltip_template.html"
#         with open(html_file, 'w', encoding='utf-8') as f:
#             f.write(html_template)
        
#         print(f"✓ Created QGIS project template: {project_file}")
#         print(f"✓ Created HTML tooltip template: {html_file}")
    
#     def generate_summary_report(self):
#         """Generate a summary report of the linking process"""
#         if self.roads_gdf is None:
#             return
            
#         total_roads = len(self.roads_gdf)
#         linked_roads = len(self.roads_gdf[self.roads_gdf['Image_URI'] != ''])
        
#         print(f"\n{'='*50}")
#         print(f"           ROAD-IMAGE LINKING SUMMARY")
#         print(f"{'='*50}")
#         print(f"Total road features:     {total_roads}")
#         print(f"Roads with images:       {linked_roads}")
#         print(f"Roads without images:    {total_roads - linked_roads}")
#         print(f"Link success rate:       {(linked_roads/total_roads)*100:.1f}%")
        
#         if linked_roads > 0:
#             distances = self.roads_gdf[self.roads_gdf['Distance_m'] != '']['Distance_m'].astype(float)
#             print(f"\nDistance Statistics:")
#             print(f"  Average distance:      {distances.mean():.1f}m")
#             print(f"  Maximum distance:      {distances.max():.1f}m")
#             print(f"  Minimum distance:      {distances.min():.1f}m")
        
#         print(f"{'='*50}")
    
#     def run_complete_workflow(self, output_shapefile, max_distance=50):
#         """
#         Execute the complete road-image linking workflow
        
#         Args:
#             output_shapefile (str): Path for output shapefile
#             max_distance (float): Maximum linking distance in meters
            
#         Returns:
#             bool: True if successful, False otherwise
#         """
#         print("🚀 Starting Road-Image Linking Workflow")
#         print("="*50)
        
#         try:
#             # Step 1: Load road shapefile
#             if not self.load_road_shapefile():
#                 return False
                
#             # Step 2: Extract image locations
#             if not self.extract_image_locations():
#                 return False
                
#             # Step 3: Reproject for accurate calculations
#             self.reproject_data()
            
#             # Step 4: Find closest images
#             matches = self.find_closest_images_to_roads(max_distance)
#             if matches == 0:
#                 print(f"✗ No matches found within {max_distance}m. Try increasing max_distance.")
#                 return False
                
#             # Step 5: Save results
#             if not self.save_updated_shapefile(output_shapefile):
#                 return False
                
#             # Step 6: Create QGIS assets
#             output_dir = Path(output_shapefile).parent
#             self.create_qgis_assets(output_dir)
            
#             # Step 7: Generate summary
#             self.generate_summary_report()
            
#             print(f"\n✅ Workflow completed successfully!")

#             # Automatically setup QGIS map tips when run from QGIS
#             try:
#                 from qgis.core import QgsProject  # Try importing PyQGIS
#                 layer_name = Path(output_shapefile).stem  # Use filename without extension
#                 html_path = str(Path(output_shapefile).parent / "image_tooltip_template.html")
                
#                 if setup_qgis_map_tips(layer_name, html_path):
#                     print("✓ QGIS map tips automatically configured")
#                 else:
#                     print("! Could not configure QGIS map tips (see previous messages)")
#             except ImportError:
#                 print("ℹ️ Not in QGIS environment - map tips can be configured later:")
#                 print(f"  1. Open {output_shapefile} in QGIS")
#                 print(f"  2. Run setup_qgis_map_tips('{Path(output_shapefile).stem}', '{html_path}') in QGIS Python console")
#             except Exception as e:
#                 print(f"⚠️ Unexpected error configuring map tips: {str(e)}")

#             return True
            
#         except Exception as e:
#             print(f"✗ Workflow failed: {e}")
#             return False


# def setup_qgis_map_tips(layer_name, html_template_path):
#     """
#     Configure QGIS map tips using PyQGIS (run in QGIS Python console)
    
#     Args:
#         layer_name (str): Name of the layer in QGIS
#         html_template_path (str): Path to HTML template file
        
#     Returns:
#         bool: True if successful, False otherwise
#     """
#     try:
#         from qgis.core import QgsProject
#         from qgis.utils import iface
        
#         # Convert to Path object and resolve absolute path
#         html_path = Path(html_template_path).resolve()
        
#         # Verify template exists
#         if not html_path.exists():
#             print(f"✗ HTML template not found: {html_path}")
#             return False
            
#         # Get the layer
#         layers = QgsProject.instance().mapLayersByName(layer_name)
#         if not layers:
#             print(f"✗ Layer '{layer_name}' not found in project")
#             return False
            
#         layer = layers[0]
        
#         try:
#             # Read HTML template with explicit encoding
#             with open(html_path, 'r', encoding='utf-8') as f:
#                 html_content = f.read()
#         except Exception as e:
#             print(f"✗ Error reading HTML template: {e}")
#             return False
        
#         # Configure map tips
#         layer.setMapTipTemplate(html_content)
#         iface.actionShowMapTips().setChecked(True)
        
#         print(f"✓ Map tips configured for layer: {layer_name}")
#         print(f"   Template: {html_path}")
#         return True
        
#     except ImportError:
#         print("✗ This function must be run within QGIS Python console")
#         print("   It requires QGIS Python environment (qgis.core, qgis.utils)")
#         return False
#     except Exception as e:
#         print(f"✗ Unexpected error setting up map tips: {e}")
#         return False


# # Example usage
# if __name__ == "__main__":
#     # Configuration
#     shapefile_path = "D:/Freelance Projects/Blue Ocean/Code/shapefile/cracking.shp"
#     images_folder = "D:/Freelance Projects/Blue Ocean/Code/pcams"
#     output_shapefile = "D:/Freelance Projects/Blue Ocean/Code/output/road_image_linked.shp"
#     max_distance = 50  # meters
    
#     # Create and run linker
#     linker = RoadImageLinker(shapefile_path, images_folder)
    
#     success = linker.run_complete_workflow(
#         output_shapefile=output_shapefile,
#         max_distance=max_distance
#     )
    
#     if success:
#         print(f"\n📋 Next Steps for QGIS:")
#         print(f"1. Open QGIS and load: {output_shapefile}")
#         print(f"2. Right-click layer → Properties → Display")
#         print(f"3. Enable 'HTML Map Tip' and load the template file")
#         print(f"4. Enable 'Show Map Tips' in View menu")
#         print(f"5. Hover over road features to see associated images")
#         print(f"\n💡 Image paths are stored in URI format for direct QGIS compatibility")
#     else:
#         print("\n❌ Workflow failed. Check error messages above.")

import os
import geopandas as gpd
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import pandas as pd
from shapely.geometry import Point
import numpy as np
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import pathname2url


class RoadImageLinker:
    """
    Links road polyline features to their closest geocoded images.
    Each road feature gets associated with exactly one closest image.
    """
    
    def __init__(self, shapefile_path, images_folder):
        """
        Initialize the Road Image Linker
        
        Args:
            shapefile_path (str): Path to the road polylines shapefile
            images_folder (str): Path to folder containing geocoded images
        """
        self.shapefile_path = Path(shapefile_path)
        self.images_folder = Path(images_folder)
        self.roads_gdf = None
        self.image_points_gdf = None
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}
        
    def _convert_to_degrees(self, dms_value):
        """
        Convert GPS DMS (Degrees, Minutes, Seconds) to decimal degrees
        
        Args:
            dms_value: Tuple of (degrees, minutes, seconds)
            
        Returns:
            float: Decimal degrees
        """
        degrees, minutes, seconds = dms_value
        return degrees + (minutes / 60.0) + (seconds / 3600.0)
    
    def _path_to_uri(self, file_path):
        """
        Convert file path to URI format
        
        Args:
            file_path (str or Path): File system path
            
        Returns:
            str: URI formatted path (file:///C:/path/to/file.jpg)
        """
        abs_path = Path(file_path).resolve()
        return urljoin('file:', pathname2url(str(abs_path)))
    
    def extract_gps_from_image(self, image_path):
        """
        Extract GPS coordinates from image EXIF data
        
        Args:
            image_path (Path): Path to the image file
            
        Returns:
            tuple: (latitude, longitude) or (None, None) if no GPS data
        """
        try:
            with Image.open(image_path) as image:
                exif_data = image._getexif()
                
                if exif_data is None:
                    return None, None
                    
                # Extract GPS info
                gps_info = {}
                for tag, value in exif_data.items():
                    decoded_tag = TAGS.get(tag, tag)
                    if decoded_tag == "GPSInfo":
                        for gps_tag in value:
                            gps_decoded = GPSTAGS.get(gps_tag, gps_tag)
                            gps_info[gps_decoded] = value[gps_tag]
                
                if not gps_info:
                    return None, None
                
                # Extract and validate coordinates
                lat_ref = gps_info.get('GPSLatitudeRef')
                lat = gps_info.get('GPSLatitude')
                lon_ref = gps_info.get('GPSLongitudeRef')
                lon = gps_info.get('GPSLongitude')
                
                if not all([lat, lon, lat_ref, lon_ref]):
                    return None, None
                
                # Convert to decimal degrees
                lat_decimal = self._convert_to_degrees(lat)
                lon_decimal = self._convert_to_degrees(lon)
                
                # Apply hemisphere corrections
                if lat_ref == 'S':
                    lat_decimal = -lat_decimal
                if lon_ref == 'W':
                    lon_decimal = -lon_decimal
                    
                return lat_decimal, lon_decimal
                
        except Exception as e:
            print(f"Warning: Could not extract GPS from {image_path.name}: {e}")
            
        return None, None
    
    def load_road_shapefile(self):
        """
        Load the road polylines shapefile
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.shapefile_path.exists():
                raise FileNotFoundError(f"Shapefile not found: {self.shapefile_path}")
                
            self.roads_gdf = gpd.read_file(self.shapefile_path)
            print(f"✓ Loaded {len(self.roads_gdf)} road features")
            print(f"  CRS: {self.roads_gdf.crs}")
            print(f"  Columns: {list(self.roads_gdf.columns)}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error loading shapefile: {e}")
            return False
    
    def extract_image_locations(self):
        """
        Extract GPS coordinates from all images in the folder
        
        Returns:
            bool: True if images with GPS found, False otherwise
        """
        if not self.images_folder.exists():
            print(f"✗ Images folder not found: {self.images_folder}")
            return False
            
        print(f"Scanning for images in: {self.images_folder}")
        
        image_data = []
        total_images = 0
        
        # Scan all image files
        for image_file in self.images_folder.rglob('*'):
            if image_file.suffix.lower() in self.supported_formats:
                total_images += 1
                lat, lon = self.extract_gps_from_image(image_file)
                
                if lat is not None and lon is not None:
                    # Convert path to URI format
                    uri_path = self._path_to_uri(image_file)
                    
                    image_data.append({
                        'image_path': str(image_file),
                        'image_uri': uri_path,
                        'filename': image_file.name,
                        'latitude': lat,
                        'longitude': lon,
                        'geometry': Point(lon, lat)
                    })
        
        print(f"  Found {total_images} image files")
        print(f"  {len(image_data)} images have GPS coordinates")
        
        if image_data:
            self.image_points_gdf = gpd.GeoDataFrame(image_data, crs='EPSG:4326')
            self._print_coordinate_summary()
            return True
        else:
            print("✗ No images with GPS data found")
            return False
    
    def _print_coordinate_summary(self):
        """Print summary of coordinate ranges for debugging"""
        if self.image_points_gdf is not None:
            bounds = self.image_points_gdf.total_bounds
            print(f"  Image coordinate bounds: [{bounds[0]:.6f}, {bounds[1]:.6f}] to [{bounds[2]:.6f}, {bounds[3]:.6f}]")
    
    def reproject_data(self, target_crs='EPSG:3857'):
        """
        Reproject data to a projected CRS for accurate distance calculations
        
        Args:
            target_crs (str): Target coordinate reference system
        """
        print("Reprojecting data for distance calculations...")
        
        # Reproject roads if geographic
        if self.roads_gdf.crs.is_geographic:
            self.roads_gdf = self.roads_gdf.to_crs(target_crs)
            print(f"  Roads reprojected to {target_crs}")
            
        # Reproject images to match roads
        if self.image_points_gdf.crs != self.roads_gdf.crs:
            self.image_points_gdf = self.image_points_gdf.to_crs(self.roads_gdf.crs)
            print(f"  Images reprojected to {self.roads_gdf.crs}")
    
    def find_closest_images_to_roads(self, max_distance=50):
        """
        Find the closest image for each road feature (one-to-one mapping)
        
        Args:
            max_distance (float): Maximum distance in meters to consider a match
            
        Returns:
            int: Number of successful matches
        """
        print(f"\nFinding closest images to roads (max distance: {max_distance}m)...")
        
        # Add image columns if they don't exist
        for col in ['Image_Path', 'Image_URI', 'Image_Name', 'Distance_m']:
            if col not in self.roads_gdf.columns:
                self.roads_gdf[col] = ''
        
        matches = []
        
        # For each road, find its closest image
        for road_idx, road_feature in self.roads_gdf.iterrows():
            # Calculate distances from this road to all images
            distances = self.image_points_gdf.geometry.distance(road_feature.geometry)
            
            if len(distances) == 0:
                continue
                
            min_distance = distances.min()
            closest_image_idx = distances.idxmin()
            
            # Only match if within maximum distance
            if min_distance <= max_distance:
                closest_image = self.image_points_gdf.iloc[closest_image_idx]
                
                matches.append({
                    'road_idx': road_idx,
                    'image_idx': closest_image_idx,
                    'distance': min_distance,
                    'image_path': closest_image['image_path'],
                    'image_uri': closest_image['image_uri'],
                    'image_name': closest_image['filename']
                })
        
        # Update roads with their closest images
        matched_roads = 0
        for match in matches:
            road_idx = match['road_idx']
            self.roads_gdf.at[road_idx, 'Image_Path'] = match['image_path']
            self.roads_gdf.at[road_idx, 'Image_URI'] = match['image_uri']
            self.roads_gdf.at[road_idx, 'Image_Name'] = match['image_name']
            self.roads_gdf.at[road_idx, 'Distance_m'] = round(match['distance'], 2)
            matched_roads += 1
        
        print(f"✓ Matched {matched_roads} roads to their closest images")
        
        # Print statistics
        if matches:
            distances = [m['distance'] for m in matches]
            print(f"  Distance statistics:")
            print(f"    Min: {min(distances):.1f}m")
            print(f"    Max: {max(distances):.1f}m")
            print(f"    Mean: {np.mean(distances):.1f}m")
            print(f"    Median: {np.median(distances):.1f}m")
        
        # Report unmatched roads
        unmatched = len(self.roads_gdf) - matched_roads
        if unmatched > 0:
            print(f"  {unmatched} roads had no images within {max_distance}m")
        
        return matched_roads
    
    def save_updated_shapefile(self, output_path):
        """
        Save the updated shapefile with image associations
        
        Args:
            output_path (str): Path for output shapefile
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert back to geographic CRS for output
            output_gdf = self.roads_gdf.to_crs('EPSG:4326')
            output_gdf.to_file(output_path)
            
            print(f"✓ Saved updated shapefile: {output_path}")
            print(f"  Added columns: Image_Path, Image_URI, Image_Name, Distance_m")
            
            return True
            
        except Exception as e:
            print(f"✗ Error saving shapefile: {e}")
            return False
    
    def create_qgis_assets(self, output_dir):
        """
        Create QGIS project template and HTML tooltip template
        
        Args:
            output_dir (str): Directory to save QGIS assets
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # QGIS Project Template
        project_template = '''<?xml version="1.0" encoding="UTF-8"?>
                                <qgis version="3.28" projectname="Road Crack Mapping">
                                <homePath path=""/>
                                <title>Road Crack Image Mapping</title>
                                <autotransaction active="0"/>
                                <evaluateDefaultValues active="0"/>
                                <trust active="0"/>
                                <projectCrs>
                                    <spatialrefsys>
                                    <wkt>GEOGCRS["WGS 84",DATUM["World Geodetic System 1984",ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],CS[ellipsoidal,2],AXIS["geodetic latitude (Lat)",north,ORDER[1],ANGLEUNIT["degree",0.0174532925199433]],AXIS["geodetic longitude (Lon)",east,ORDER[2],ANGLEUNIT["degree",0.0174532925199433]],USAGE[SCOPE["Horizontal component of 3D system."],AREA["World."],BBOX[-90,-180,90,180]],ID["EPSG",4326]]</wkt>
                                    <proj4>+proj=longlat +datum=WGS84 +no_defs</proj4>
                                    <srsid>3452</srsid>
                                    <srid>4326</srid>
                                    <authid>EPSG:4326</authid>
                                    <description>WGS 84</description>
                                    <projectionacronym>longlat</projectionacronym>
                                    <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
                                    <geographicflag>true</geographicflag>
                                    </spatialrefsys>
                                </projectCrs>
                                </qgis>'''
        
        project_file = output_dir / "road_image_mapping.qgs"
        with open(project_file, 'w', encoding='utf-8') as f:
            f.write(project_template)
        
        # HTML Template for Map Tips (using URI format)
        html_template = '''<!DOCTYPE html>
                            <html>
                            <head>
                                <style>
                                    body { 
                                        margin: 5px; 
                                        font-family: Arial, sans-serif; 
                                        background: #f9f9f9;
                                        border-radius: 5px;
                                        padding: 10px;
                                    }
                                    .header {
                                        font-weight: bold;
                                        color: #333;
                                        margin-bottom: 10px;
                                        border-bottom: 1px solid #ddd;
                                        padding-bottom: 5px;
                                    }
                                    .image-container { 
                                        text-align: center;
                                        margin: 10px 0;
                                    }
                                    .road-image { 
                                        max-width: 300px; 
                                        max-height: 200px; 
                                        border: 2px solid #007cba;
                                        border-radius: 4px;
                                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                    }
                                    .image-info {
                                        font-size: 11px;
                                        color: #666;
                                        margin-top: 5px;
                                        background: white;
                                        padding: 5px;
                                        border-radius: 3px;
                                    }
                                    .distance {
                                        font-weight: bold;
                                        color: #007cba;
                                    }
                                    .no-image {
                                        color: #999;
                                        font-style: italic;
                                        text-align: center;
                                        padding: 20px;
                                    }
                                </style>
                            </head>
                            <body>
                                [% CASE WHEN "Image_URI" IS NOT NULL AND "Image_URI" != '' THEN %]
                                    <div class="header">Road Crack Image</div>
                                    <div class="image-container">
                                        <img src="[% "Image_URI" %]" alt="Road crack image" class="road-image">
                                        <div class="image-info">
                                            <div><strong>File:</strong> [% "Image_Name" %]</div>
                                            <div><strong>Distance:</strong> <span class="distance">[% "Distance_m" %]m</span></div>
                                        </div>
                                    </div>
                                [% ELSE %]
                                    <div class="no-image">No image associated with this road segment</div>
                                [% END %]
                            </body>
                            </html>'''
        
        html_file = output_dir / "image_tooltip_template.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        print(f"✓ Created QGIS project template: {project_file}")
        print(f"✓ Created HTML tooltip template: {html_file}")
    
    def generate_summary_report(self):
        """Generate a summary report of the linking process"""
        if self.roads_gdf is None:
            return
            
        total_roads = len(self.roads_gdf)
        linked_roads = len(self.roads_gdf[self.roads_gdf['Image_URI'] != ''])
        
        print(f"\n{'='*50}")
        print(f"           ROAD-IMAGE LINKING SUMMARY")
        print(f"{'='*50}")
        print(f"Total road features:     {total_roads}")
        print(f"Roads with images:       {linked_roads}")
        print(f"Roads without images:    {total_roads - linked_roads}")
        print(f"Link success rate:       {(linked_roads/total_roads)*100:.1f}%")
        
        if linked_roads > 0:
            distances = self.roads_gdf[self.roads_gdf['Distance_m'] != '']['Distance_m'].astype(float)
            print(f"\nDistance Statistics:")
            print(f"  Average distance:      {distances.mean():.1f}m")
            print(f"  Maximum distance:      {distances.max():.1f}m")
            print(f"  Minimum distance:      {distances.min():.1f}m")
        
        print(f"{'='*50}")
    
    def run_complete_workflow(self, output_shapefile, max_distance=50):
        """
        Execute the complete road-image linking workflow
        
        Args:
            output_shapefile (str): Path for output shapefile
            max_distance (float): Maximum linking distance in meters
            
        Returns:
            bool: True if successful, False otherwise
        """
        print("🚀 Starting Road-Image Linking Workflow")
        print("="*50)
        
        try:
            # Step 1: Load road shapefile
            if not self.load_road_shapefile():
                return False
                
            # Step 2: Extract image locations
            if not self.extract_image_locations():
                return False
                
            # Step 3: Reproject for accurate calculations
            self.reproject_data()
            
            # Step 4: Find closest images
            matches = self.find_closest_images_to_roads(max_distance)
            if matches == 0:
                print(f"✗ No matches found within {max_distance}m. Try increasing max_distance.")
                return False
                
            # Step 5: Save results
            if not self.save_updated_shapefile(output_shapefile):
                return False
                
            # Step 6: Create QGIS assets
            output_dir = Path(output_shapefile).parent
            self.create_qgis_assets(output_dir)
            
            # Step 7: Generate summary
            self.generate_summary_report()
            
            print(f"\n✅ Workflow completed successfully!")

            # Automatically setup QGIS map tips when run from QGIS
            # Define html_path outside the try block to fix variable scope issue
            layer_name = Path(output_shapefile).stem
            html_path = str(Path(output_shapefile).parent / "image_tooltip_template.html")
            
            try:
                from qgis.core import QgsProject  # Try importing PyQGIS
                
                if setup_qgis_map_tips(layer_name, html_path):
                    print("✓ QGIS map tips automatically configured")
                else:
                    print("! Could not configure QGIS map tips (see previous messages)")
            except ImportError:
                print("ℹ️ Not in QGIS environment - map tips can be configured later:")
                print(f"  1. Open {output_shapefile} in QGIS")
                print(f"  2. Run setup_qgis_map_tips('{layer_name}', '{html_path}') in QGIS Python console")
            except Exception as e:
                print(f"⚠️ Unexpected error configuring map tips: {str(e)}")

            return True
            
        except Exception as e:
            print(f"✗ Workflow failed: {e}")
            return False


def setup_qgis_map_tips(layer_name, html_template_path):
    """
    Configure QGIS map tips using PyQGIS (run in QGIS Python console)
    
    Args:
        layer_name (str): Name of the layer in QGIS
        html_template_path (str): Path to HTML template file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from qgis.core import QgsProject
        from qgis.utils import iface
        
        # Convert to Path object and resolve absolute path
        html_path = Path(html_template_path).resolve()
        
        # Verify template exists
        if not html_path.exists():
            print(f"✗ HTML template not found: {html_path}")
            return False
            
        # Get the layer
        layers = QgsProject.instance().mapLayersByName(layer_name)
        if not layers:
            print(f"✗ Layer '{layer_name}' not found in project")
            return False
            
        layer = layers[0]
        
        try:
            # Read HTML template with explicit encoding
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            print(f"✗ Error reading HTML template: {e}")
            return False
        
        # Configure map tips
        layer.setMapTipTemplate(html_content)
        iface.actionShowMapTips().setChecked(True)
        
        print(f"✓ Map tips configured for layer: {layer_name}")
        print(f"   Template: {html_path}")
        return True
        
    except ImportError:
        print("✗ This function must be run within QGIS Python console")
        print("   It requires QGIS Python environment (qgis.core, qgis.utils)")
        return False
    except Exception as e:
        print(f"✗ Unexpected error setting up map tips: {e}")
        return False


# Example usage
if __name__ == "__main__":
    # Configuration
    shapefile_path = "D:/Freelance Projects/Blue Ocean/Code/shapefile/cracking.shp"
    images_folder = "D:/Freelance Projects/Blue Ocean/Code/pcams"
    output_shapefile = "D:/Freelance Projects/Blue Ocean/Code/output/road_image_linked.shp"
    max_distance = 50  # meters
    
    # Create and run linker
    linker = RoadImageLinker(shapefile_path, images_folder)
    
    success = linker.run_complete_workflow(
        output_shapefile=output_shapefile,
        max_distance=max_distance
    )
    
    if success:
        print(f"\n📋 Next Steps for QGIS:")
        print(f"1. Open QGIS and load: {output_shapefile}")
        print(f"2. Right-click layer → Properties → Display")
        print(f"3. Enable 'HTML Map Tip' and load the template file")
        print(f"4. Enable 'Show Map Tips' in View menu")
        print(f"5. Hover over road features to see associated images")
        print(f"\n💡 Image paths are stored in URI format for direct QGIS compatibility")
    else:
        print("\n❌ Workflow failed. Check error messages above.")