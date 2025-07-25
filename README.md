# Dataset 3D hydrogeological model of the Mexico Basin
This dataset includes 10 GemPy models that were used to build the regional hydrogeological model of the Mexico Basin using Python. It also contains Python scripts used to transform GIS information into the format required by GemPy.


## Tabla de Contenidos
1. [Installation](#installation)
2. [Usage](#usage)
3. [Project Structure](#project-structure)
4. [LICENSE](#license)
5. [Contact](#contact)

## Installation

  ### Clone the repository
  git clone https://github.com/Nauj29/GemPy_Model_Mexico_Basin.git

  ### Navigate to the project directory
  cd GemPy_Model_Mexico_Basin

  ### Install the dependencies
  pip install -r requirements.txt

## Usage
  This dataset is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License. It can be used for academic and research purposes only. Commercial use is not allowed without prior permission from the authors.

  ### Python Scripts
  Python and master scripts were developed to automate the modification of hydrogeological sections and the generation of GemPy inputs.

  #### Modification of hydrogeological sections
      •	01_Extend_faults.py
      •	02_Calculate_apparent_dip.py
      •	03_Add_faults.py
      •	04_Add_original_sections.py
      •	05_process_interfaces.py
      •	06_Master_1.py

  #### Creation of Gempy Inputs from Hydrogeological sections modified
      •	07_Gempy_plant.py
      •	08_Gempy_Merge_sections.py
      •	09_Gempy_Int.py
      •	10_Gempy_Ori.py
      •	11_Master_2.py
  
  ####  Full automation of the process
          •	12_Master_3.py

  ### How to use
  To execute the Python scripts, users need to provide the model subregion (e.g., North, Middle, or South) as a command-line argument. This argument must exactly match the name of the corresponding folder and shapefile for the selected subregion. For instance, to run the fault extension script for the Middle subregion, the command would be: python 01_Extend_faults.py Middle. In contrast, when using the Master Scripts, specifying the subregion manually is not required, as the selection is handled automatically within the workflow.

## Project Structure
  ```plaintext
  GemPy_Model_Mexico_Basin/
  │
  ├── Dataset/      # "Hydrogeological Sections (Shapefiles) – Mexico Basin [Dataset], https://doi.org/10.5281/zenodo.14619021."
  │   ├──Hydrogeological_Units/
  │                 ├──lineal/               # Line shapefiles for hydrogeological units
  │                 ├──Polygon/              # Polygon shapefiles for hydrogeological units
  │   ├──Surface/                            # Surface-related data or shapefiles
  │   ├──Raster/                             # Digital elevation model (DEM)
  │
  ├── Notebooks/                             # Jupyter notebooks named according to the modeled zone
  ├── Results/                               # Final outputs of the GemPy models, such as NumPy arrays and vtk files
  │         ├──txt/
  │         ├──vtk/
  │
  ├── Scripts/                               # Contains all the Python scripts
  ├── Shapefiles/                            # Contains all intermediate shapefiles by regions 
  │         ├──Middle/
  │               ├──Final/                  # Includes a finalized section of hydrogeological units
  │               ├──Gempy/                  # Contains all sections merged into one
  │               ├──Modified/               # Contains a section of hydrogeological units modified by the addition of faults
  │         ├──North/
  │               ├──Final/
  │               ├──Gempy/
  │               ├──Modified/
  │         ├──South/
  │               ├──Final/
  │               ├──Gempy/
  │               ├──Modified/
  ├── Tables                                 # This includes all intermediate .txt files, grouped by region. 
  │         ├──Middle/
  │                ├──Clipped/               # This includes all .txt files, grouped by model area. 
  │         ├──North/
  │                ├──Clipped/
  │         ├──South/
  │                ├──Clipped/
  │  
  ├── README.md                 # Instructions file
  ├── requirements.txt          # Project dependencies
  ├── LICENSE                   # File License

  ```
## LICENSE
  Creative Commons Attribution 4.0 International License

  You are free to:
  - Share — copy and redistribute the material in any medium or format
  - Adapt — remix, transform, and build upon the material

  Under the following terms:
  - Attribution — You must give appropriate credit, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses   you or your use. [DOI:10.5281/zenodo.13852434](https://doi.org/10.5281/zenodo.13852434)


## Contact
jcmontanoc@comunidad.unam.mx

