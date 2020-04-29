"""Transformer for creating mosaics
"""

import argparse
import logging
import os
import subprocess

import terrautils.lemnatec

import shadeRemoval as shade

import transformer_class    # pylint: disable=import-error

terrautils.lemnatec.SENSOR_METADATA_CACHE = os.path.dirname(os.path.realpath(__file__))

class __internal__():
    """Internal use only class
    """
    def __init(self):
        """Performs class instance initialization
        """

    @staticmethod
    def create_vrt_permanent(base_dir: str, file_list: str, out_vrt: str = 'virtualTif.vrt', alpha: bool = False) -> None:
        """Creates a VRT file to allow further processing of files
        Arguments:
            base_dir: the path to the working folder
            file_list: the path to the file containing the list of files to process
            out_vrt: the name of the vrt file to create
            alpha: set to True to generate an alpha layer mask from the image
        Notes:
            Pure black pixels will create a full transparent value, all other values have no transparency at all.
            Ported from original full_day_to_tiles.py file
        """
        # Create virtual tif for the files in this folder
        # Build a virtual TIF that combines all of the tifs that we just created
        logging.debug("Creating virtual TIF: %s", out_vrt)
        vrt_path = os.path.join(base_dir, out_vrt)
        if alpha:
            cmd = 'gdalbuildvrt -addalpha -srcnodata "-99 -99 -99" -overwrite -input_file_list ' + file_list + ' ' + vrt_path
        else:
            cmd = 'gdalbuildvrt -srcnodata "-99 -99 -99" -overwrite -input_file_list ' + file_list +' ' + vrt_path
        logging.debug("Running Virtual Tiff command: '%s'", cmd)
        cmd_result = os.system(cmd)
        logging.debug('Result of Virtual Tiff command: %s', cmd_result)

    @staticmethod
    def generate_single_mosaic(**kwargs) -> tuple:
        """Creates a mosaic from a list of files
        Arguments (all are referenced as keyword arguments and therefore must be explicitly named):
            thumb_only: a boolean value indicating only thumbnails get generated
            bounds: a string containing the upper left and lower right boundaries of the mosaic
            out_dir: folder for resulting mosaic
            file_list_path: the path to the file containing the list of files making up the mosaic
            out_vrt: the vrt file to use
            out_thumb: the name of the thumbnail file
            out_full: the name of the full mosaic file
            out_medium: the name of the medium sized mosaic file
        Return:
            A list containing the list of images created as the first element the the total size of the image files
        """
        logging.debug("Creating mosaic")

        files_created, sum_bytes = [], 0
        bounds = kwargs['bounds']

        # Create VRT from every GeoTIFF
        out_vrt_filename = kwargs['out_vrt']
        out_vrt = os.path.join(kwargs['out_dir'], kwargs['out_vrt'])
        logging.info("Creating VRT %s...", out_vrt)
        if out_vrt.endswith("_mask.vrt"):
            __internal__.create_vrt_permanent(kwargs['out_dir'], kwargs['file_list_path'], out_vrt_filename, alpha=True)
        else:
            __internal__.create_vrt_permanent(kwargs['out_dir'], kwargs['file_list_path'], out_vrt_filename)
        files_created.append(out_vrt)
        sum_bytes += os.path.getsize(out_vrt)

        # Omit _mask.vrt from 2%
        if not out_vrt.endswith('_mask.vrt'):
            cur_out_file = os.path.join(kwargs['out_dir'], kwargs['out_thumb'])
            logging.info("Converting VRT to %s...", cur_out_file)
            cmd = "gdal_translate -co COMPRESS=LZW -co BIGTIFF=YES -projwin %s -outsize %s%% %s%% '%s' '%s'" % \
                    (bounds, 2, 2, out_vrt, cur_out_file)
            logging.debug("Thumbnail command: '%s'", cmd)
            subprocess.call(cmd, shell=True)
            files_created.append(cur_out_file)
            sum_bytes += os.path.getsize(cur_out_file)

        # Only process other resolutions if thumbnails-only not specified
        if not kwargs['thumb_only']:
            # Omit _mask.vrt and _nrmac.vrt from 10%
            if not (out_vrt.endswith('_mask.vrt') or out_vrt.endswith('_nrmac.vrt')):
                cur_out_file = os.path.join(kwargs['out_dir'], kwargs['out_medium'])
                logging.info("Converting VRT to %s...", cur_out_file)
                cmd = "gdal_translate -co COMPRESS=LZW -co BIGTIFF=YES -projwin %s -outsize %s%% %s%% '%s' '%s'" % \
                        (bounds, 10, 10, out_vrt, cur_out_file)
                logging.debug("Medium command: '%s'", cmd)
                subprocess.call(cmd, shell=True)
                files_created.append(cur_out_file)
                sum_bytes += os.path.getsize(cur_out_file)

            # Omit _nrmac.vrt from 100%
            if not out_vrt.endswith('_nrmac.vrt'):
                cur_out_file = os.path.join(kwargs['out_dir'], kwargs['out_full'])
                logging.info("Converting VRT to %s...", cur_out_file)
                cmd = "gdal_translate -co COMPRESS=LZW -co BIGTIFF=YES -projwin %s '%s' '%s'" % \
                        (bounds, out_vrt, cur_out_file)
                logging.debug("Full command: '%s'", cmd)
                subprocess.call(cmd, shell=True)
                files_created.append(cur_out_file)
                sum_bytes += os.path.getsize(cur_out_file)

        return files_created, sum_bytes

    @staticmethod
    def generate_darker_mosaic(**kwargs) -> tuple:
        """Creates a darkened mosaic from a list of files
        Arguments (all are referenced as keyword arguments and therefore must be explicitly named):
            thumb_only: a boolean value indicating only thumbnails get generated
            bounds: a string containing the upper left and lower right boundaries of the mosaic
            split: the spit size for generating darker images
            out_dir: folder for resulting mosaic
            file_list_path: the path to the file containing the list of files making up the mosaic
            out_vrt: the vrt file to use
            out_thumb: the name of the thumbnail file
            out_full: the name of the full mosaic file
            out_medium: the name of the medium sized mosaic file
        Return:
            A list containing the list of images created as the first element the the total size of the image files
        """
        logging.debug("Creating darker mosaic")

        # Create dark-pixel mosaic from geotiff list using multipass for darker pixel selection
        files_created, sum_bytes = [], 0
        bounds = kwargs['bounds']
        out_dir = kwargs['out_dir']
        split = kwargs['split']

        # Create VRT from every GeoTIFF
        out_vrt_filename = kwargs['out_vrt']
        out_vrt = os.path.join(kwargs['out_dir'], kwargs['out_vrt'])
        logging.info("Creating VRT %s...", out_vrt)
        __internal__.create_vrt_permanent(kwargs['out_dir'], kwargs['file_list_path'], out_vrt_filename)
        files_created.append(out_vrt)
        sum_bytes += os.path.getsize(out_vrt)

        # Split full file_list_path into parts according to split number
        shade.split_tif_list(kwargs['file_list_path'], out_dir, split)

        # Generate tiles from each split VRT into numbered folders
        shade.create_diff_tiles_set(out_dir, split)

        # Choose darkest pixel from each overlapping tile
        unite_tiles_dir = os.path.join(out_dir, 'unite')
        if not os.path.exists(unite_tiles_dir):
            os.mkdir(unite_tiles_dir)
        shade.integrate_tiles(out_dir, unite_tiles_dir, split)

        # If any files didn't have overlap, copy individual tile
        shade.copy_missing_tiles(out_dir, unite_tiles_dir, split)

        # Create output VRT from overlapped tiles
        out_vrt = os.path.join(out_dir, kwargs['out_vrt'])
        shade.create_unite_tiles(unite_tiles_dir, out_vrt)
        files_created.append(out_vrt)
        sum_bytes += os.path.getsize(out_vrt)

        cur_out_file = os.path.join(out_dir, kwargs['out_thumb'])
        logging.info("Converting VRT to %s...", cur_out_file)
        cmd = "gdal_translate -projwin %s -outsize %s%% %s%% '%s' '%s'" % (bounds, 2, 2, out_vrt, cur_out_file)
        logging.debug("Thumbnail command: '%s'", cmd)
        subprocess.call(cmd, shell=True)
        files_created.append(cur_out_file)
        sum_bytes += os.path.getsize(cur_out_file)

        if not kwargs['thumb_only']:
            cur_out_file = os.path.join(out_dir, kwargs['out_medium'])
            logging.info("Converting VRT to %s...", cur_out_file)
            cmd = "gdal_translate -projwin %s -outsize %s%% %s%% '%s' '%s'" % (bounds, 10, 10, out_vrt, cur_out_file)
            logging.debug("Medium command: '%s'", cmd)
            subprocess.call(cmd, shell=True)
            files_created.append(cur_out_file)
            sum_bytes += os.path.getsize(cur_out_file)

            cur_out_file = os.path.join(out_dir, kwargs['out_full'])
            logging.info("Converting VRT to %s...", cur_out_file)
            cmd = "gdal_translate -projwin %s '%s' '%s'" % (bounds, out_vrt, cur_out_file)
            logging.debug("Full command: '%s'", cmd)
            subprocess.call(cmd, shell=True)
            files_created.append(cur_out_file)
            sum_bytes += os.path.getsize(cur_out_file)

        return files_created, sum_bytes

def add_parameters(parser: argparse.ArgumentParser) -> None:
    """Adds parameters
    Arguments:
        parser: instance of argparse
    """
    parser.add_argument('--darker', type=bool, default=os.getenv('MOSAIC_DARKER', None),
                        help='whether to use multipass mosiacking to select darker pixels')
    parser.add_argument('--split', type=int, default=os.getenv('MOSAIC_SPLIT', '2'),
                        help='number of splits to use if --darker is to true')
    parser.add_argument('--thumb', action='store_true',
                        help='whether to only generate a 2 percent thumbnail image')
    parser.add_argument('mosaic_list_file', type=str, help='path to a text file containing a list of source file paths for the mosaic')
    parser.add_argument('sensor', type=str,
                        help='the name of the sensor associated with the metadata (stereoTop, flirIrCamera, scanner3DTop)')
    parser.add_argument('mosaic_bounds', type=str, help='the geographic bounds of the mosaic to generate (EPSG 4326 coordinates)')

def perform_process(transformer: transformer_class.Transformer, check_md: dict, transformer_md: dict, full_md: dict) -> dict:
    """Performs the processing of the data
    Arguments:
        transformer: instance of transformer class
    Return:
        Returns a dictionary with the results of processing
    """
    # pylint: disable=unused-argument
    sensor = transformer.args.sensor
    if sensor == 'stereoTop':
        sensor_lookup = 'rgb_fullfield'
        output_file_ext = '.tif'
    elif sensor == 'flirIrCamera':
        sensor_lookup = 'ir_fullfield'
        output_file_ext = '.tif'
    elif sensor == 'scanner3DTop':
        sensor_lookup = 'laser3d_fullfield'
        output_file_ext = '.tif'
    else:
        msg = "Invalid sensor specified for mosaic: '%s'" % sensor
        logging.debug(msg)
        return {'code': -1000, 'error': msg}

    # Perform actual field stitching
    out_filename = "fullfield_mosaic"
    out_png = out_filename + ".png"

    params = {
        'thumb_only': transformer.args.thumb,
        'bounds': transformer.args.mosaic_bounds,
        'split': transformer.args.split,
        'out_dir': check_md['working_folder'],
        'file_list_path': transformer.args.mosaic_list_file,
        'out_vrt': out_filename + '.vrt',
        'out_thumb': out_filename + "_thumb" + output_file_ext,
        'out_full': out_filename + output_file_ext,
        'out_medium': out_filename + "_10pct" + output_file_ext,
    }
    if not transformer.args.darker or sensor_lookup != 'rgb_fullfield':
        (files_created, num_bytes) = __internal__.generate_single_mosaic(**params)
    else:
        (files_created, num_bytes) = __internal__.generate_darker_mosaic(**params)

    if not transformer.args.thumb and os.path.isfile(os.path.join(params['out_dir'], params['out_medium'])):
        # Create PNG thumbnail
        logging.info("Converting 10pct to %s...", out_png)
        png_file = os.path.join(check_md['working_folder'], out_png)
        cmd = "gdal_translate -of PNG %s %s" % \
                (os.path.join(check_md['working_folder'], params['out_medium']), png_file)
        logging.debug("PNG command: '%s'", cmd)
        subprocess.call(cmd, shell=True)
        files_created.append(png_file)
        num_bytes += os.path.getsize(png_file)

    # Setup the return list of files
    files_list = []
    for one_file in files_created:
        files_list.append(
            {
                'path': one_file,
                'key': sensor
            })

    return {
        'file': files_list,
        'code': 0,
    }
