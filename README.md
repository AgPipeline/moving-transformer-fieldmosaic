# Transformer: RGB Mosaic

Creates a mosaic image from a series of individual frames.

### Uses 

the stitched image, as is, is good for:

#### Evaluating data quality and valid sensor operation

- Understanding what part of the field was imaged,
- Understanding if the imaging script is correctly capturing the plots (in the context of not imaging the whole field), or if there is a problem it is missing some of the plots.
- Understanding if the image capture has good lighting, no motion blur, etc.

#### Data analysis: computing some phenotypes

- an extractor for Canopy Coverage Percentage, and
- an extractor for some other phenotype analyses such as emergence date, leaf color, flower/panacle detection


#### Data analysis: the stitched image is not appropriate for some analyses 

- Any stitched image introduces new artifacts into the image data; it always introduces edges at the boundary of where one image turns into another --- either an explicitly black line boundary or an implicit boundary that is there because you can't exactly stitch images of a complicated 3D world (without making a full 3D model).  Even if you could stitch them (say, it is just flat dirt), the same bit of the world is usually a different brightness when viewed from different directions.
- The particular stitching strategy of "choose the darker pixel" is a nice way to automatically choose a good image when there is bright sunshine effects.  It may create additional artifacts because the algorithm is allowed to integrate pixels from both images in potentially complicated patterns.  These artifacts may be hard to account for.
- The alternative is to always to all initial feature selection or image analysis on the original images, and to then create derived features or extracted features from those images and save those derived or extracted features per plot.

To ground this discussion, here is an example of a stitched image

![picture1](https://user-images.githubusercontent.com/20230686/26936199-916d6b64-4c33-11e7-8544-97294aa97017.png)

## Failure Conditions

### Image Stitching Artifacts
One of the artifacts is duplication of area, this is unavoidable without a much more complex stitching algorithm that implicitly infers the 3D structure of the ground. The justification for not going for such a rich representation is that:
* for the plants, since they move, it would be impossible not to have artifacts at the edges of the image, and
* for the ground, I judged that small stitching errors were not worth the (substantial) additional effort to build the more complete model.

Related Issues and Discussions

* Review of RGB Full Field extractor https://github.com/terraref/reference-data/issues/183
* Dealing with sun/shade https://github.com/terraref/computing-pipeline/issues/326
* Robert Pless https://github.com/terraref/computing-pipeline/issues/326#issuecomment-314895910,
https://github.com/terraref/computing-pipeline/issues/326#issuecomment-314592669, https://github.com/terraref/reference-data/issues/183#issuecomment-330697397

### Sample Docker Command Line
Below is a sample command line that shows how the field mosaic Docker image could be run.
An explanation of the command line options used follows.
Be sure to read up on the [docker run](https://docs.docker.com/engine/reference/run/) command line for more information.

```docker run --rm --mount "src=/home/test,target=/mnt,type=bind" agpipeline/fieldmosaic:2.0 --working_space "/mnt" --metadata "/mnt/08f445ef-b8f9-421a-acf1-8b8c206c1bb8_metadata_cleaned.json" "/mnt/source_files.txt" "stereoTop" "-111.9750963 33.0764953 -111.9747967 33.074485715"```

This example command line assumes the source files are located in the `/home/test` folder of the local machine.
The name of the image to run is `agpipeline/fieldmosaic:2.0`.

We are using the same folder for the source files and the output files.
By using multiple `--mount` options, the source and output files can be separated.

**Docker commands** \
Everything between 'docker' and the name of the image are docker commands.

- `run` indicates we want to run an image
- `--rm` automatically delete the image instance after it's run
- `--mount "src=/home/test,target=/mnt,type=bind"` mounts the `/home/test` folder to the `/mnt` folder of the running image

We mount the `/home/test` folder to the running image to make files available to the software in the image.

**Image's commands** \
The command line parameters after the image name are passed to the software inside the image.
Note that the paths provided are relative to the running image (see the --mount option specified above).

- `--working_space "/mnt"` specifies the folder to use as a workspace
- `--metadata "/mnt/08f445ef-b8f9-421a-acf1-8b8c206c1bb8_metadata.cleaned.json"` is the name of the source metadata to be cleaned
- `"/mnt/source_files.txt"` contains the list of files (relative to the image: /mnt in this example) to include in the mosaic
- `"stereoTop"` the name of the sensor associated with the source files
- `"-111.9750963 33.0764953 -111.9747967 33.074485715"` the geographic boundaries of the image mosaic (upper left and lower right corner positions)

### Sample Masking Docker Command Line
Use the `--mask` flag if you wish to have a masking Alpha channel added to the generated Orthomosaic.
The generated Alpha channel will have full opaqueness for pixels that are black.
All other Alpha channel pixels have full transparency.

The following example command line builds off the previous example and illustrates the use of the `--mask` flag.

```docker run --rm --mount "src=/home/test,target=/mnt,type=bind" agpipeline/fieldmosaic:2.0 --mask --working_space "/mnt" --metadata "/mnt/08f445ef-b8f9-421a-acf1-8b8c206c1bb8_metadata_cleaned.json" "/mnt/source_files_mask.txt" "stereoTop" "-111.9750963 33.0764953 -111.9747967 33.074485715"```

A comparison with the previous command line shows that the `--mask` command line option and the name of the input file `source_files_mask.txt` are different.
The name of the input file was changed to help illustrate the input differences between the two commands; it can remain the same.
