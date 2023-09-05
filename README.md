# Sentinel Image Explorer (SIE)

## Description

This Python code provides a custom QGIS plugin widget that allows users to interact with time-series mosaics from Sentinel. It includes functionalities like filtering images by date, zooming to a specific point, and a time-lapse feature that plays through the mosaics in time order. Additionally, it includes a Layer Grid view to display small previews of all layers in a grid.

![Sentinel Image Explorer ](./sie.gif)

## Features

- Filter Planet's mosaics by date range
- Time-lapse playback through the mosaics
- Zoom to a specific point
- Layer Grid for a quick overview
- Play, Stop, and Remove Layers buttons

## Prerequisites

- Make sure you have QGIS installed on your system  ([Download](https://qgis.org/en/site/forusers/download.html)).
- Install the lib `satsearch` to search images Sentinel

## Installing satsearch in QGIS Python Environment on Windows

`satsearch` is a Python library for discovering public satellite imagery. This README provides step-by-step instructions for installing `satsearch` within the Python environment used by QGIS on Windows.

### Prerequisites

- Command Prompt with administrative rights

### Steps

#### Step 1: Locate QGIS Python Executable

1. Locate the Python executable associated with your QGIS installation. The path often resembles:

    ```
    C:\Program Files\QGIS XXX\apps\Python39\
    ```

    **Note:** Replace `XXX` with your specific QGIS version number.

#### Step 2: Open Command Prompt as Administrator

1. Navigate to the start menu, search for "Command Prompt", right-click on it and select "Run as administrator".

#### Step 3: Install `satsearch`

1. In the Command Prompt, execute the following command to install `satsearch` using pip. Replace `path_to_qgis_python` with the actual path you found in Step 1.

    ```bash
    C:\path_to_qgis_python\python.exe -m pip install satsearch
    ```

    This will install `satsearch` into the Python environment used by QGIS.

#### Step 4: Verify Installation

1. Verify the installation by executing:

    ```bash
    C:\path_to_qgis_python\python.exe -m pip show satsearch
    ```

    This should display information about the installed package, including its version.

#### Step 5: Import in QGIS

1. You can now use `satsearch` in your QGIS Python scripts as shown below:

    ```python
    from satsearch import Search
    ```

#### Troubleshooting

- If you encounter permissions or access rights errors, ensure that you are running the Command Prompt as an administrator.
- If `pip` is not found, it may need to be installed in your QGIS Python environment. Installation methods can vary based on your QGIS version.

#### Further Resources

- [satsearch GitHub Repository](https://github.com/sat-utils/sat-search)
- [QGIS Website](https://qgis.org)

## Installing satsearch in QGIS Python Environment on Windows Manually

### Sub-section: Adding `satsearch` and `satstac` to QGIS Python Environment

When you cannot install the `satsearch` and `satstac` packages directly into your QGIS Python environment using package managers like `pip`, you can manually add these libraries. This involves downloading the directories from a specific GitHub repository and then copying them to the appropriate location within the QGIS Python environment.

### Prerequisites

1. You need administrative rights to copy files into `C:\Program Files\QGIS XXX\apps\Python39\Lib`.
2. Internet access to download `satsearch` and `satstac` directories from the GitHub repository.

### Steps

#### 1. Download the Directories

- Go to the GitHub repository at [https://github.com/tharlestsa/qgis-sie](https://github.com/tharlestsa/qgis-sie).
- Download the repository to your local machine, either by using the 'Download ZIP' option or by cloning the repository using Git.

#### 2. Locate the Downloaded Directories

Unzip the downloaded repository and navigate to the location where the `satsearch` and `satstac` folders are stored.

#### 3. Locate the QGIS Python Environment

- Open File Explorer and navigate to the Python environment folder inside your QGIS installation, usually located at `C:\Program Files\QGIS XXX\apps\Python39\Lib`. 
- Here, `XXX` refers to the version of QGIS you have installed.

#### 4. Copy the Directories

- Right-click on the `satsearch` folder and choose `Copy`.
- Navigate back to the `C:\Program Files\QGIS XXX\apps\Python39\Lib` directory.
- Right-click in the folder and choose `Paste` to copy the `satsearch` folder here.

Repeat these steps for the `satstac` folder.

#### 5. Administrative Rights

If prompted, confirm that you have the administrative rights to copy files into this directory.

#### 6. Verify the Installation

To ensure that the libraries are correctly installed, you can open the QGIS Python console and try importing `satsearch` and `satstac` by typing the following commands:

```python
import satsearch
import satstac
```

## Install the Plugin via Python Console

1. Open QGIS.
2. Open the Python Console (`Plugins -> Python Console` or press `Ctrl+Alt+P`).
3. Go to the `Show Editor` tab.
4. Copy-paste the script `sie.py` into the editor and run it.

## Usage

1. Open the widget from your QGIS interface.
2. Use the date filters to set a start and end date for the mosaics.
3. Optionally, enter coordinates to zoom to a specific point.
4. Use the Play button to start a time-lapse through the mosaics.
5. Use the Stop button to stop the time-lapse.
6. Use the Grid button to view a grid of all layers.
7. Use the Remove Layers button to remove all the current layers from the project.

## License

This project is open source and available under the MIT License.

## Acknowledgements

This plugin makes use of data and software services from several organizations and platforms. We are grateful for their support and the valuable resources they provide.

**QGIS**: This plugin would not have been possible without the robust and open-source capabilities of QGIS. Special thanks to the QGIS development community for providing the software and resources that make advanced geospatial analysis accessible. More information about QGIS can be found on their [official website](https://qgis.org/).

### Data Providers

- **Copernicus Sentinel**: The Sentinel satellite data used in this project is part of the Copernicus program by the European Space Agency. For more information, visit [Copernicus Open Access Hub](https://scihub.copernicus.eu/).

### APIs

- **Earth Search**: We use the Earth Search API by Element 84 for querying Sentinel data. Their STAC-compliant API provides easy and fast access to satellite imagery. For more information, check their API documentation at [Earth Search API](https://earth-search.aws.element84.com/v0).

### Software Libraries

- **titiler**: This project uses titiler for dynamic tiling of geospatial data. Developed by Development Seed, titiler provides a high-performance, customizable solution for serving raster data. View the source code and documentation on their [GitHub repository](https://github.com/developmentseed/titiler).



